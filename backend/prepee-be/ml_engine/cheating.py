"""
Cheating Detection Engine
===========================
Multi-signal anomaly detection system:
1. Time Anomaly: Suspiciously fast answers
2. Score Spike: Sudden accuracy jumps
3. Answer Pattern: Repeated answer positions
4. Isolation Forest: ML-based anomaly detection

Flags are stored in CheatingFlag model with severity 0.0-1.0
"""
import logging
from collections import Counter

import numpy as np

logger = logging.getLogger(__name__)


class TimeAnomalyDetector:
    """Detects suspiciously fast response times."""

    ABSOLUTE_MIN_SECONDS = 2.0     # Impossible to read + answer under 2s
    FAST_THRESHOLD_RATIO = 0.25    # < 25% of avg time = suspicious

    def detect(self, attempts_data, avg_time_global=30.0):
        """
        Args:
            attempts_data: list of dicts with 'time_taken_seconds' and 'is_correct'
            avg_time_global: global average time per question
        Returns:
            dict with score and evidence
        """
        if not attempts_data:
            return {'score': 0.0, 'evidence': [], 'flag': False}

        times = [a['time_taken_seconds'] for a in attempts_data]
        correct = [a['is_correct'] for a in attempts_data]

        # Count impossibly fast correct answers
        fast_correct = 0
        evidence = []
        for i, (t, c) in enumerate(zip(times, correct)):
            if c and t < self.ABSOLUTE_MIN_SECONDS:
                fast_correct += 1
                evidence.append(f"Q{i+1}: correct in {t:.1f}s (< {self.ABSOLUTE_MIN_SECONDS}s)")
            elif c and t < avg_time_global * self.FAST_THRESHOLD_RATIO:
                fast_correct += 1
                evidence.append(f"Q{i+1}: correct in {t:.1f}s (< {avg_time_global * self.FAST_THRESHOLD_RATIO:.1f}s threshold)")

        ratio = fast_correct / len(attempts_data) if attempts_data else 0
        score = min(1.0, ratio * 3.0)  # Scale up: 33% fast answers = 1.0 severity

        return {
            'score': round(score, 4),
            'fast_correct_count': fast_correct,
            'total_questions': len(attempts_data),
            'evidence': evidence[:10],
            'flag': score > 0.3,
        }


class ScoreSpikeDetector:
    """Detects sudden jumps in accuracy that are statistically unlikely."""

    WINDOW_SIZE = 10
    SPIKE_THRESHOLD = 0.5  # 50% accuracy jump between windows

    def detect(self, attempts_data):
        if len(attempts_data) < self.WINDOW_SIZE * 2:
            return {'score': 0.0, 'evidence': [], 'flag': False}

        correctness = [1 if a['is_correct'] else 0 for a in attempts_data]

        # Compare sliding windows
        max_spike = 0.0
        evidence = []
        for i in range(len(correctness) - self.WINDOW_SIZE * 2 + 1):
            window1 = correctness[i:i + self.WINDOW_SIZE]
            window2 = correctness[i + self.WINDOW_SIZE:i + self.WINDOW_SIZE * 2]

            acc1 = sum(window1) / self.WINDOW_SIZE
            acc2 = sum(window2) / self.WINDOW_SIZE
            spike = acc2 - acc1

            if spike > self.SPIKE_THRESHOLD:
                max_spike = max(max_spike, spike)
                evidence.append(f"Window {i+1}-{i+self.WINDOW_SIZE}: {acc1:.0%} → {acc2:.0%} (+{spike:.0%})")

        score = min(1.0, max_spike / 0.7)

        return {
            'score': round(score, 4),
            'max_spike': round(max_spike, 4),
            'evidence': evidence[:5],
            'flag': score > 0.3,
        }


class AnswerPatternDetector:
    """Detects suspicious answer position patterns (e.g. always picking 'B')."""

    def detect(self, attempts_data):
        if len(attempts_data) < 10:
            return {'score': 0.0, 'evidence': [], 'flag': False}

        answers = [a.get('selected_index', 0) for a in attempts_data]
        counter = Counter(answers)
        total = len(answers)

        # Check for dominant single answer
        most_common_answer, most_common_count = counter.most_common(1)[0]
        dominance_ratio = most_common_count / total

        evidence = []
        if dominance_ratio > 0.5:
            evidence.append(f"Answer '{most_common_answer}' selected {dominance_ratio:.0%} of the time")

        # Check for sequential repeats
        max_streak = 1
        current_streak = 1
        for i in range(1, len(answers)):
            if answers[i] == answers[i - 1]:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        if max_streak >= 5:
            evidence.append(f"Same answer repeated {max_streak} times consecutively")

        pattern_score = max(0, (dominance_ratio - 0.35) / 0.4) * 0.6
        streak_score = max(0, (max_streak - 3) / 7) * 0.4
        score = min(1.0, pattern_score + streak_score)

        return {
            'score': round(score, 4),
            'dominant_answer_ratio': round(dominance_ratio, 4),
            'max_streak': max_streak,
            'evidence': evidence[:5],
            'flag': score > 0.3,
        }


class IsolationForestDetector:
    """ML-based anomaly detection using Isolation Forest."""

    def __init__(self):
        self._model = None

    def detect(self, student_features):
        """
        Args:
            student_features: dict with 'accuracy', 'avg_time', 'total_attempts',
                            'fast_answer_ratio', 'score_variance'
        """
        try:
            features = np.array([[
                student_features.get('accuracy', 0.5),
                student_features.get('avg_time', 30),
                student_features.get('total_attempts', 50),
                student_features.get('fast_answer_ratio', 0.0),
                student_features.get('score_variance', 0.1),
            ]])

            if self._model is None:
                self._load_or_train_model()

            if self._model is None:
                return {'score': 0.0, 'evidence': ['Model not available'], 'flag': False}

            anomaly_score = self._model.decision_function(features)[0]
            # Isolation Forest: negative = anomaly, positive = normal
            # Convert to 0-1 severity (lower decision_function = higher severity)
            severity = max(0.0, min(1.0, -anomaly_score))

            is_anomaly = self._model.predict(features)[0] == -1

            return {
                'score': round(severity, 4),
                'raw_anomaly_score': round(float(anomaly_score), 4),
                'is_anomaly': bool(is_anomaly),
                'evidence': [f"Isolation Forest anomaly score: {anomaly_score:.4f}"],
                'flag': is_anomaly,
            }

        except Exception as e:
            logger.warning(f"IsolationForest detection failed: {e}")
            return {'score': 0.0, 'evidence': [str(e)], 'flag': False}

    def _load_or_train_model(self):
        """Load trained model or train on current data."""
        from pathlib import Path
        import joblib

        model_path = Path(__file__).parent / 'trained_models' / 'cheating_isolation_forest.pkl'

        if model_path.exists():
            self._model = joblib.load(model_path)
            return

        # Train on current data
        self._train_and_save(model_path)

    def _train_and_save(self, model_path):
        """Train Isolation Forest on student aggregate features."""
        from sklearn.ensemble import IsolationForest
        from ml_engine.models import StudentProfile
        import joblib

        profiles = StudentProfile.objects.filter(total_questions_attempted__gte=10)
        if profiles.count() < 20:
            return

        features = []
        for p in profiles:
            features.append([
                p.accuracy_rate,
                p.avg_time_per_question,
                p.total_questions_attempted,
                0.0,  # fast_answer_ratio (computed separately)
                0.1,  # score_variance placeholder
            ])

        X = np.array(features)
        self._model = IsolationForest(
            n_estimators=100, contamination=0.05, random_state=42
        )
        self._model.fit(X)

        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._model, model_path)
        logger.info(f"Trained Isolation Forest on {len(features)} profiles, saved to {model_path}")


class HybridCheatingDetector:
    """Combines all detection signals into a composite cheating score."""

    WEIGHTS = {
        'time_anomaly': 0.35,
        'score_spike': 0.25,
        'answer_pattern': 0.20,
        'isolation_forest': 0.20,
    }

    def __init__(self):
        self.time_detector = TimeAnomalyDetector()
        self.spike_detector = ScoreSpikeDetector()
        self.pattern_detector = AnswerPatternDetector()
        self.forest_detector = IsolationForestDetector()

    def analyze_match(self, user, match):
        """Analyze a single match for cheating signals."""
        from ml_engine.models import QuestionAttempt, CheatingFlag, StudentProfile

        attempts = QuestionAttempt.objects.filter(student=user, match=match).order_by('created_at')
        if not attempts.exists():
            return None

        attempts_data = []
        for a in attempts:
            q = a.question
            options = q.options if q.options else []
            selected_idx = options.index(a.selected_answer) if a.selected_answer in options else 0

            attempts_data.append({
                'time_taken_seconds': a.time_taken_seconds,
                'is_correct': a.is_correct,
                'selected_index': selected_idx,
            })

        # Run all detectors
        time_result = self.time_detector.detect(attempts_data)
        spike_result = self.spike_detector.detect(attempts_data)
        pattern_result = self.pattern_detector.detect(attempts_data)

        # Isolation Forest needs aggregate features
        profile = StudentProfile.objects.filter(user=user).first()
        forest_input = {
            'accuracy': profile.accuracy_rate if profile else 0.5,
            'avg_time': profile.avg_time_per_question if profile else 30,
            'total_attempts': profile.total_questions_attempted if profile else 0,
            'fast_answer_ratio': time_result.get('fast_correct_count', 0) / max(1, len(attempts_data)),
            'score_variance': 0.1,
        }
        forest_result = self.forest_detector.detect(forest_input)

        # Composite score
        composite = (
            time_result['score'] * self.WEIGHTS['time_anomaly'] +
            spike_result['score'] * self.WEIGHTS['score_spike'] +
            pattern_result['score'] * self.WEIGHTS['answer_pattern'] +
            forest_result['score'] * self.WEIGHTS['isolation_forest']
        )

        # Determine flag type
        scores = {
            'time_anomaly': time_result['score'],
            'score_spike': spike_result['score'],
            'answer_pattern': pattern_result['score'],
        }
        dominant_signal = max(scores, key=scores.get) if any(v > 0.3 for v in scores.values()) else 'composite'

        result = {
            'composite_score': round(composite, 4),
            'should_flag': composite > 0.25,
            'dominant_signal': dominant_signal,
            'details': {
                'time_anomaly': time_result,
                'score_spike': spike_result,
                'answer_pattern': pattern_result,
                'isolation_forest': forest_result,
            }
        }

        # Create CheatingFlag if threshold exceeded
        if composite > 0.25:
            flag_type = dominant_signal if dominant_signal != 'composite' else 'composite'
            CheatingFlag.objects.create(
                user=user,
                match=match,
                flag_type=flag_type,
                severity=composite,
                details=result['details'],
            )

        return result

    def scan_all_students(self, stdout=None):
        """Scan all students using Isolation Forest for bulk anomaly detection."""
        from ml_engine.models import StudentProfile, CheatingFlag

        profiles = StudentProfile.objects.filter(total_questions_attempted__gte=10)
        flagged = 0

        for profile in profiles:
            features = {
                'accuracy': profile.accuracy_rate,
                'avg_time': profile.avg_time_per_question,
                'total_attempts': profile.total_questions_attempted,
                'fast_answer_ratio': 0.0,
                'score_variance': 0.1,
            }

            result = self.forest_detector.detect(features)

            if result.get('is_anomaly'):
                flagged += 1
                if stdout:
                    stdout.write(f"  🚩 {profile.user.username}: anomaly score {result['score']:.4f}")

        if stdout:
            stdout.write(f"Scanned {profiles.count()} students, flagged {flagged} anomalies.")

        return {'total_scanned': profiles.count(), 'flagged': flagged}
