"""
Synthetic Data Generator
=========================
Generates realistic simulated data for ML model training:
- 500 students with ELO 800-1600, subject-specific strengths
- 50,000 QuestionAttempts with realistic correctness/time distributions
- ~3% cheater profiles with suspicious patterns

Usage:
    python manage.py generate_synthetic_data --students 500 --attempts 50000
"""
import random
import math
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()

SUBJECTS = ['Physics', 'Chemistry', 'Biology', 'Mathematics', 'English', 'Logical Reasoning', 'ECAT', 'MCAT']


def sigmoid(x):
    return 1 / (1 + math.exp(-max(-10, min(10, x))))


class SyntheticDataGenerator:
    """Generates realistic synthetic student data for ML training."""

    def __init__(self, num_students=500, num_attempts=50000, cheater_ratio=0.03):
        self.num_students = num_students
        self.num_attempts = num_attempts
        self.cheater_ratio = cheater_ratio
        self.students = []
        self.cheater_ids = set()

    def generate_all(self, stdout=None):
        """Run the full generation pipeline."""
        from ml_engine.models import Question, QuestionAttempt, StudentProfile

        questions = list(Question.objects.all())
        if not questions:
            msg = "No questions in database. Run 'python manage.py seed_questions' first."
            if stdout:
                stdout.write(msg)
            raise ValueError(msg)

        self._log(stdout, f"Found {len(questions)} questions in database.")

        # Step 1: Generate students
        self._log(stdout, f"Generating {self.num_students} synthetic students...")
        self._generate_students()

        # Step 2: Generate attempts
        self._log(stdout, f"Generating {self.num_attempts} question attempts...")
        attempts = self._generate_attempts(questions)

        # Step 3: Bulk create attempts
        self._log(stdout, f"Saving {len(attempts)} attempts to database...")
        QuestionAttempt.objects.bulk_create(attempts, batch_size=1000)

        # Step 4: Update student profiles
        self._log(stdout, "Updating student profiles...")
        self._update_profiles()

        # Step 5: Update question difficulty scores from actual performance
        self._log(stdout, "Updating question difficulty scores from performance data...")
        self._update_question_difficulties(questions)

        self._log(stdout, f"Done! Generated {self.num_students} students, {len(attempts)} attempts, {len(self.cheater_ids)} cheaters.")

        return {
            'students': self.num_students,
            'attempts': len(attempts),
            'cheaters': len(self.cheater_ids),
            'questions': len(questions),
        }

    def _generate_students(self):
        """Create synthetic User + StudentProfile records."""
        from ml_engine.models import StudentProfile

        num_cheaters = int(self.num_students * self.cheater_ratio)

        for i in range(self.num_students):
            username = f"student_{i+1:04d}"
            email = f"{username}@prepee.synthetic"

            # Skip if user already exists
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
            else:
                elo = int(random.gauss(1200, 200))
                elo = max(800, min(1600, elo))

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='synthetic_pass_123',
                    elo=elo,
                )

            # Assign subject strengths (3 strong, 2-3 weak)
            strong_subjects = random.sample(SUBJECTS, 3)
            strengths = {}
            for subj in SUBJECTS:
                if subj in strong_subjects:
                    strengths[subj] = round(random.uniform(0.65, 0.95), 2)
                else:
                    strengths[subj] = round(random.uniform(0.25, 0.55), 2)

            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={'subject_strengths': strengths}
            )

            is_cheater = i < num_cheaters
            if is_cheater:
                self.cheater_ids.add(user.id)

            self.students.append({
                'user': user,
                'profile': profile,
                'elo': user.elo,
                'strengths': strengths,
                'is_cheater': is_cheater,
                'base_time': random.uniform(15, 45),
            })

    def _generate_attempts(self, questions):
        """Generate realistic QuestionAttempt records."""
        from ml_engine.models import QuestionAttempt
        from ml_engine.difficulty import HybridDifficultyCalculator

        calculator = HybridDifficultyCalculator()
        attempts = []
        attempts_per_student = self.num_attempts // self.num_students

        for student_data in self.students:
            user = student_data['user']
            n_attempts = attempts_per_student + random.randint(-10, 10)

            for _ in range(max(1, n_attempts)):
                question = random.choice(questions)

                # Get difficulty
                q_difficulty = question.difficulty_score if question.difficulty_score > 0 else 0.5

                if student_data['is_cheater']:
                    # Cheater behavior
                    is_correct = random.random() < 0.95
                    time_taken = random.uniform(0.5, 3.0)
                else:
                    # Normal behavior
                    student_ability = (student_data['elo'] - 800) / 800  # 0.0-1.0
                    subject_bonus = student_data['strengths'].get(question.subject, 0.5) - 0.5
                    p_correct = sigmoid(2.5 * (student_ability - q_difficulty + subject_bonus))
                    is_correct = random.random() < p_correct

                    # Time taken: harder = longer, with noise
                    difficulty_mult = 0.7 + q_difficulty * 1.5
                    noise = max(0.3, random.gauss(1.0, 0.3))
                    time_taken = student_data['base_time'] * difficulty_mult * noise
                    time_taken = max(2, min(120, time_taken))

                # Select answer
                if is_correct:
                    selected = question.options[question.correct_answer_index]
                else:
                    wrong_indices = [i for i in range(len(question.options)) if i != question.correct_answer_index]
                    if wrong_indices:
                        selected = question.options[random.choice(wrong_indices)]
                    else:
                        selected = question.options[0]

                attempts.append(QuestionAttempt(
                    student=user,
                    question=question,
                    selected_answer=selected,
                    is_correct=is_correct,
                    time_taken_seconds=round(time_taken, 2),
                    created_at=timezone.now(),
                ))

        random.shuffle(attempts)
        return attempts

    def _update_profiles(self):
        """Update StudentProfile with computed stats from attempts."""
        from ml_engine.models import QuestionAttempt, StudentProfile

        for student_data in self.students:
            user = student_data['user']
            attempts = QuestionAttempt.objects.filter(student=user)

            if not attempts.exists():
                continue

            total = attempts.count()
            correct = attempts.filter(is_correct=True).count()
            avg_time = attempts.values_list('time_taken_seconds', flat=True)
            avg_time = sum(avg_time) / len(avg_time) if avg_time else 30.0

            # Subject strengths from actual data
            subject_strengths = {}
            for subj in SUBJECTS:
                subj_attempts = attempts.filter(question__subject=subj)
                if subj_attempts.exists():
                    subj_correct = subj_attempts.filter(is_correct=True).count()
                    subject_strengths[subj] = round(subj_correct / subj_attempts.count(), 4)

            profile = student_data['profile']
            profile.total_questions_attempted = total
            profile.accuracy_rate = round(correct / total, 4) if total > 0 else 0
            profile.avg_time_per_question = round(avg_time, 2)
            profile.subject_strengths = subject_strengths
            profile.save()

    def _update_question_difficulties(self, questions):
        """Update each question's difficulty_score based on actual success rate."""
        from ml_engine.models import QuestionAttempt

        for question in questions:
            attempts = QuestionAttempt.objects.filter(question=question)
            if attempts.exists():
                total = attempts.count()
                correct = attempts.filter(is_correct=True).count()
                observed_difficulty = 1.0 - (correct / total)
                question.difficulty_score = round(observed_difficulty, 4)
                question.save(update_fields=['difficulty_score'])

    def _log(self, stdout, msg):
        if stdout:
            stdout.write(msg)
        logger.info(msg)
