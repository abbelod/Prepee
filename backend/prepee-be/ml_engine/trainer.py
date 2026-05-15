"""
ML Model Trainer
=================
Trains Difficulty Prediction models using generated synthetic data.
Models: Random Forest + XGBoost (ensemble/comparison).
Saves trained models to ml_engine/trained_models/ as .pkl files.
"""
import os
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)
MODEL_DIR = Path(__file__).parent / 'trained_models'


class DifficultyTrainer:
    """Trains Random Forest + XGBoost models for difficulty prediction."""

    BLOOM_MAP = {'recall': 0, 'understand': 1, 'apply': 2, 'analyze': 3, 'evaluate': 4}
    SUBJECT_MAP = {
        'Physics': 0, 'Chemistry': 1, 'Biology': 2, 'Mathematics': 3,
        'English': 4, 'Logical Reasoning': 5, 'ECAT': 6, 'MCAT': 7,
    }

    def __init__(self):
        self.rf_model = None
        self.xgb_model = None
        self.metrics = {}

    def prepare_data(self, stdout=None):
        """Extract features from Question + QuestionAttempt data."""
        from ml_engine.models import Question, QuestionAttempt
        from ml_engine.difficulty import TextComplexityAnalyzer, BloomDetector

        text_analyzer = TextComplexityAnalyzer()
        bloom_detector = BloomDetector()

        questions = Question.objects.all()
        if not questions.exists():
            raise ValueError("No questions found. Run seed_questions first.")

        rows = []
        for q in questions:
            text_result = text_analyzer.analyze(q.text)
            bloom_result = bloom_detector.detect(q.text)

            # Performance-based difficulty (target variable)
            attempts = QuestionAttempt.objects.filter(question=q)
            if attempts.exists():
                total = attempts.count()
                correct = attempts.filter(is_correct=True).count()
                actual_difficulty = 1.0 - (correct / total)
                avg_time = attempts.values_list('time_taken_seconds', flat=True)
                avg_time = sum(avg_time) / len(avg_time)
            else:
                actual_difficulty = q.difficulty_score
                avg_time = 30.0

            rows.append({
                'question_id': q.id,
                'text_complexity': text_result['complexity_score'],
                'bloom_level_encoded': self.BLOOM_MAP.get(bloom_result['bloom_level'], 0),
                'subject_encoded': self.SUBJECT_MAP.get(q.subject, 0),
                'word_count': text_result['word_count'],
                'avg_word_length': text_result['avg_word_length'],
                'technical_terms': text_result['technical_terms'],
                'formula_present': 1 if text_result['formula_present'] else 0,
                'negation_count': text_result['negation_count'],
                'option_count': len(q.options) if q.options else 4,
                'avg_response_time': avg_time,
                'actual_difficulty': actual_difficulty,
            })

        df = pd.DataFrame(rows)
        self._log(stdout, f"Prepared {len(df)} training samples with {len(df.columns)} features.")
        return df

    def train(self, stdout=None):
        """Train both RF and XGBoost models."""
        df = self.prepare_data(stdout)

        feature_cols = [
            'text_complexity', 'bloom_level_encoded', 'subject_encoded',
            'word_count', 'avg_word_length', 'technical_terms',
            'formula_present', 'negation_count', 'option_count',
            'avg_response_time',
        ]
        X = df[feature_cols].values
        y = df['actual_difficulty'].values

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # ── Random Forest ──
        self._log(stdout, "Training Random Forest Regressor...")
        self.rf_model = RandomForestRegressor(
            n_estimators=200, max_depth=10, min_samples_split=5,
            min_samples_leaf=2, random_state=42, n_jobs=-1,
        )
        self.rf_model.fit(X_train, y_train)
        rf_pred = self.rf_model.predict(X_test)
        rf_metrics = self._compute_regression_metrics(y_test, rf_pred, 'RandomForest')
        self._log(stdout, f"  RF — MAE: {rf_metrics['mae']:.4f}, R²: {rf_metrics['r2']:.4f}")

        # Feature importance
        importances = dict(zip(feature_cols, self.rf_model.feature_importances_))
        rf_metrics['feature_importances'] = {k: round(v, 4) for k, v in sorted(importances.items(), key=lambda x: -x[1])}

        # Cross-validation
        cv_scores = cross_val_score(self.rf_model, X, y, cv=5, scoring='neg_mean_absolute_error')
        rf_metrics['cv_mae_mean'] = round(-cv_scores.mean(), 4)
        rf_metrics['cv_mae_std'] = round(cv_scores.std(), 4)
        self._log(stdout, f"  RF — 5-fold CV MAE: {rf_metrics['cv_mae_mean']:.4f} ± {rf_metrics['cv_mae_std']:.4f}")

        # ── XGBoost ──
        self._log(stdout, "Training XGBoost Regressor...")
        try:
            from xgboost import XGBRegressor
            self.xgb_model = XGBRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8,
                random_state=42, verbosity=0,
            )
            self.xgb_model.fit(X_train, y_train)
            xgb_pred = self.xgb_model.predict(X_test)
            xgb_metrics = self._compute_regression_metrics(y_test, xgb_pred, 'XGBoost')
            self._log(stdout, f"  XGB — MAE: {xgb_metrics['mae']:.4f}, R²: {xgb_metrics['r2']:.4f}")
        except ImportError:
            self._log(stdout, "  XGBoost not available, skipping.")
            xgb_metrics = {'model': 'XGBoost', 'status': 'skipped'}

        # ── Save models ──
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        rf_path = MODEL_DIR / 'difficulty_model.pkl'
        joblib.dump(self.rf_model, rf_path)
        self._log(stdout, f"  Saved RF model to {rf_path}")

        if self.xgb_model:
            xgb_path = MODEL_DIR / 'difficulty_xgboost.pkl'
            joblib.dump(self.xgb_model, xgb_path)
            self._log(stdout, f"  Saved XGB model to {xgb_path}")

        # Save feature order for inference
        meta_path = MODEL_DIR / 'difficulty_features.pkl'
        joblib.dump(feature_cols, meta_path)

        self.metrics = {
            'random_forest': rf_metrics,
            'xgboost': xgb_metrics,
            'dataset_size': len(df),
            'train_size': len(X_train),
            'test_size': len(X_test),
        }

        return self.metrics

    def _compute_regression_metrics(self, y_true, y_pred, model_name):
        """Compute standard regression metrics."""
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)

        # Also bin into easy/medium/hard for classification metrics
        def bin_difficulty(scores):
            return ['easy' if s < 0.33 else 'hard' if s > 0.66 else 'medium' for s in scores]

        y_true_binned = bin_difficulty(y_true)
        y_pred_binned = bin_difficulty(y_pred)

        accuracy = accuracy_score(y_true_binned, y_pred_binned)
        f1 = f1_score(y_true_binned, y_pred_binned, average='weighted', zero_division=0)

        return {
            'model': model_name,
            'mae': round(mae, 4),
            'rmse': round(rmse, 4),
            'r2': round(r2, 4),
            'binned_accuracy': round(accuracy, 4),
            'binned_f1': round(f1, 4),
        }

    def _log(self, stdout, msg):
        if stdout:
            stdout.write(msg)
        logger.info(msg)
