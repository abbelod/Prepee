"""
Recommendation Engine
======================
Hybrid recommender: Content-Based + Collaborative Filtering.

Strategy:
1. Content-Based: Recommends questions from weak subjects/topics at appropriate difficulty.
2. Collaborative: Finds similar students and recommends questions they answered correctly.
3. Hybrid: Combines both with configurable weights.
"""
import random
import logging
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)


class StudentProfiler:
    """Computes and updates student ML profiles from attempt data."""

    def update_profile(self, user):
        """Recompute a student's profile from their attempts."""
        from ml_engine.models import QuestionAttempt, StudentProfile

        attempts = QuestionAttempt.objects.filter(student=user)
        if not attempts.exists():
            return

        profile, _ = StudentProfile.objects.get_or_create(user=user)

        total = attempts.count()
        correct = attempts.filter(is_correct=True).count()

        # Subject strengths
        subject_strengths = {}
        topic_strengths = {}
        subjects = attempts.values_list('question__subject', flat=True).distinct()
        for subj in subjects:
            subj_attempts = attempts.filter(question__subject=subj)
            subj_correct = subj_attempts.filter(is_correct=True).count()
            subject_strengths[subj] = round(subj_correct / subj_attempts.count(), 4)

            # Topics within subject
            topics = subj_attempts.values_list('question__topic', flat=True).distinct()
            for topic in topics:
                topic_attempts = subj_attempts.filter(question__topic=topic)
                topic_correct = topic_attempts.filter(is_correct=True).count()
                topic_strengths[f"{subj}/{topic}"] = round(topic_correct / topic_attempts.count(), 4)

        # Average time
        times = list(attempts.values_list('time_taken_seconds', flat=True))
        avg_time = sum(times) / len(times) if times else 30.0

        profile.total_questions_attempted = total
        profile.accuracy_rate = round(correct / total, 4) if total > 0 else 0
        profile.avg_time_per_question = round(avg_time, 2)
        profile.subject_strengths = subject_strengths
        profile.topic_strengths = topic_strengths
        profile.save()

        return profile


class ContentBasedRecommender:
    """Recommends questions targeting student's weak areas."""

    def recommend(self, user, profile, n=10):
        from ml_engine.models import Question, QuestionAttempt

        weak_subjects = profile.get_weakest_subjects(3) if profile.subject_strengths else []

        if not weak_subjects:
            candidates = Question.objects.order_by('?')[:n]
            return {
                'question_ids': [{'id': q.id} for q in candidates],
                'strategy': 'random (no profile data)',
                'weaknesses': [],
            }

        # Get questions from weak subjects, not recently attempted
        recent_q_ids = list(
            QuestionAttempt.objects.filter(student=user)
            .order_by('-created_at')[:50]
            .values_list('question_id', flat=True)
        )

        candidates = (
            Question.objects.filter(subject__in=weak_subjects)
            .exclude(id__in=recent_q_ids)
            .order_by('difficulty_score')
        )

        # Adaptive difficulty: target slightly above student's current level
        student_accuracy = profile.accuracy_rate
        target_difficulty = max(0.3, min(0.8, 1.0 - student_accuracy + 0.1))

        scored = []
        for q in candidates[:100]:
            # Score based on distance from target difficulty
            diff_match = 1.0 - abs(q.difficulty_score - target_difficulty)
            # Bonus for weak subjects
            weakness_bonus = 1.0 - profile.subject_strengths.get(q.subject, 0.5)
            score = diff_match * 0.6 + weakness_bonus * 0.4
            scored.append((q, score))

        scored.sort(key=lambda x: -x[1])
        selected = [q for q, _ in scored[:n]]

        return {
            'question_ids': [{'id': q.id} for q in selected],
            'strategy': 'content-based (weakness targeting)',
            'weaknesses': weak_subjects,
            'target_difficulty': round(target_difficulty, 2),
        }


class CollaborativeRecommender:
    """Finds similar students and recommends what worked for them."""

    def recommend(self, user, profile, n=10):
        from ml_engine.models import Question, QuestionAttempt, StudentProfile

        # Find students with similar accuracy
        similar_profiles = (
            StudentProfile.objects
            .exclude(user=user)
            .filter(
                accuracy_rate__gte=profile.accuracy_rate - 0.15,
                accuracy_rate__lte=profile.accuracy_rate + 0.15,
            )[:20]
        )

        if not similar_profiles.exists():
            return {'question_ids': [], 'strategy': 'collaborative (no similar students)', 'weaknesses': []}

        similar_user_ids = [p.user_id for p in similar_profiles]

        # Questions that similar students answered correctly but this student hasn't attempted
        attempted_ids = set(
            QuestionAttempt.objects.filter(student=user)
            .values_list('question_id', flat=True)
        )

        good_questions = (
            QuestionAttempt.objects
            .filter(student_id__in=similar_user_ids, is_correct=True)
            .exclude(question_id__in=attempted_ids)
            .values_list('question_id', flat=True)
        )

        # Count how many similar students got each right
        question_scores = defaultdict(int)
        for qid in good_questions:
            question_scores[qid] += 1

        top_q_ids = sorted(question_scores, key=question_scores.get, reverse=True)[:n]
        questions = Question.objects.filter(id__in=top_q_ids)

        return {
            'question_ids': [{'id': q.id} for q in questions],
            'strategy': 'collaborative (similar student success)',
            'similar_students_found': len(similar_user_ids),
        }


class HybridRecommender:
    """Combines content-based and collaborative recommendations."""

    def __init__(self, content_weight=0.6, collab_weight=0.4):
        self.content = ContentBasedRecommender()
        self.collab = CollaborativeRecommender()
        self.profiler = StudentProfiler()
        self.content_weight = content_weight
        self.collab_weight = collab_weight

    def recommend(self, user, n=10):
        from ml_engine.models import StudentProfile

        profile, created = StudentProfile.objects.get_or_create(user=user)
        if created or profile.total_questions_attempted == 0:
            self.profiler.update_profile(user)
            profile.refresh_from_db()

        content_result = self.content.recommend(user, profile, n=n)
        collab_result = self.collab.recommend(user, profile, n=n)

        # Merge and deduplicate
        seen = set()
        merged = []

        # Add content-based (weighted more)
        content_count = int(n * self.content_weight)
        for item in content_result['question_ids'][:content_count]:
            if item['id'] not in seen:
                seen.add(item['id'])
                merged.append(item)

        # Fill with collaborative
        for item in collab_result['question_ids']:
            if len(merged) >= n:
                break
            if item['id'] not in seen:
                seen.add(item['id'])
                merged.append(item)

        # If still short, add from content
        for item in content_result['question_ids']:
            if len(merged) >= n:
                break
            if item['id'] not in seen:
                seen.add(item['id'])
                merged.append(item)

        return {
            'question_ids': merged[:n],
            'strategy': f'hybrid (content={self.content_weight}, collab={self.collab_weight})',
            'weaknesses': content_result.get('weaknesses', []),
        }

    def get_practice_set(self, user, n=10):
        """Generate a focused practice set for weak areas."""
        from ml_engine.models import StudentProfile, Question

        profile, _ = StudentProfile.objects.get_or_create(user=user)

        weak_subjects = profile.get_weakest_subjects(2)
        if not weak_subjects:
            weak_subjects = ['Physics', 'Mathematics']

        questions = (
            Question.objects
            .filter(subject__in=weak_subjects)
            .filter(difficulty_score__gte=0.3, difficulty_score__lte=0.7)
            .order_by('?')[:n]
        )

        return {
            'question_ids': [q.id for q in questions],
            'focus_areas': weak_subjects,
            'difficulty_range': {'min': 0.3, 'max': 0.7},
        }
