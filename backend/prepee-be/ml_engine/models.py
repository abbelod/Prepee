from django.db import models
from django.conf import settings


class Question(models.Model):
    """Proper question storage — replaces hardcoded JSON questions."""

    SUBJECT_CHOICES = [
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Biology', 'Biology'),
        ('Mathematics', 'Mathematics'),
        ('English', 'English'),
        ('Logical Reasoning', 'Logical Reasoning'),
        ('ECAT', 'ECAT'),
        ('MCAT', 'MCAT'),
    ]

    BLOOM_LEVEL_CHOICES = [
        ('recall', 'Recall'),
        ('understand', 'Understand'),
        ('apply', 'Apply'),
        ('analyze', 'Analyze'),
        ('evaluate', 'Evaluate'),
    ]

    text = models.TextField(help_text="The question text")
    options = models.JSONField(help_text='List of answer options, e.g. ["opt1", "opt2", "opt3", "opt4"]')
    correct_answer_index = models.IntegerField(help_text="0-based index of the correct answer in options list")
    explanation = models.TextField(blank=True, default='', help_text="Explanation for the correct answer")
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, db_index=True)
    topic = models.CharField(max_length=100, db_index=True, help_text="Specific topic within the subject")
    difficulty_score = models.FloatField(
        default=0.5,
        help_text="Auto-calculated difficulty: 0.0 = Very Easy, 1.0 = Very Hard"
    )
    text_complexity = models.FloatField(default=0.5, help_text="Flesch-Kincaid based text complexity score")
    bloom_level = models.CharField(
        max_length=20,
        choices=BLOOM_LEVEL_CHOICES,
        default='recall',
        help_text="Bloom's Taxonomy cognitive level"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subject', 'topic', 'difficulty_score']
        indexes = [
            models.Index(fields=['subject', 'difficulty_score']),
            models.Index(fields=['topic', 'difficulty_score']),
        ]

    def __str__(self):
        return f"[{self.subject}/{self.topic}] {self.text[:80]}..."

    @property
    def correct_answer(self):
        """Returns the text of the correct answer."""
        if self.options and 0 <= self.correct_answer_index < len(self.options):
            return self.options[self.correct_answer_index]
        return None


class QuestionAttempt(models.Model):
    """Tracks every student answer — the core ML training data source."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='question_attempts'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    match = models.ForeignKey(
        'matchmaking.Match',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='question_attempts'
    )
    selected_answer = models.CharField(max_length=500, help_text="The answer the student selected")
    is_correct = models.BooleanField(help_text="Whether the selected answer was correct")
    time_taken_seconds = models.FloatField(help_text="Time in seconds to answer this question")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'question']),
            models.Index(fields=['student', 'is_correct']),
            models.Index(fields=['question', 'is_correct']),
        ]

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.student.username} → Q{self.question_id} ({self.time_taken_seconds:.1f}s)"


class StudentProfile(models.Model):
    """Cached ML profile per student — updated after each quiz submission."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ml_profile'
    )
    subject_strengths = models.JSONField(
        default=dict,
        help_text='Per-subject accuracy, e.g. {"Physics": 0.85, "Biology": 0.42}'
    )
    topic_strengths = models.JSONField(
        default=dict,
        help_text='Per-topic accuracy, e.g. {"Mechanics": 0.90, "Optics": 0.35}'
    )
    avg_time_per_question = models.FloatField(
        default=30.0,
        help_text="Average seconds per question across all attempts"
    )
    total_questions_attempted = models.IntegerField(default=0)
    accuracy_rate = models.FloatField(
        default=0.0,
        help_text="Overall accuracy (0.0 to 1.0)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Student profiles'

    def __str__(self):
        return f"Profile: {self.user.username} (Acc: {self.accuracy_rate:.0%}, Q: {self.total_questions_attempted})"

    def get_weakest_subjects(self, n=3):
        """Returns the N weakest subjects by accuracy."""
        if not self.subject_strengths:
            return []
        sorted_subjects = sorted(self.subject_strengths.items(), key=lambda x: x[1])
        return [s[0] for s in sorted_subjects[:n]]

    def get_strongest_subjects(self, n=3):
        """Returns the N strongest subjects by accuracy."""
        if not self.subject_strengths:
            return []
        sorted_subjects = sorted(self.subject_strengths.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_subjects[:n]]


class CheatingFlag(models.Model):
    """Records suspicious activity detected by the cheating detection engine."""

    FLAG_TYPE_CHOICES = [
        ('time_anomaly', 'Time Anomaly'),
        ('score_spike', 'Score Spike'),
        ('answer_pattern', 'Answer Pattern'),
        ('composite', 'Composite (Multiple Signals)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cheating_flags'
    )
    match = models.ForeignKey(
        'matchmaking.Match',
        on_delete=models.CASCADE,
        related_name='cheating_flags'
    )
    flag_type = models.CharField(max_length=30, choices=FLAG_TYPE_CHOICES, db_index=True)
    severity = models.FloatField(
        help_text="Cheating probability score: 0.0 = unlikely, 1.0 = almost certain"
    )
    details = models.JSONField(
        help_text="Detailed breakdown of anomaly scores and evidence"
    )
    reviewed = models.BooleanField(default=False, help_text="Whether an admin has reviewed this flag")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['user', 'flag_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['reviewed']),
        ]

    def __str__(self):
        return f"🚩 {self.user.username} | {self.flag_type} | Severity: {self.severity:.2f}"
