from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Train all ML models (difficulty prediction, cheating detection)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("  PREPEE ML MODEL TRAINING PIPELINE"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))

        # 1. Train difficulty prediction
        self.stdout.write("\n📊 [1/3] Training Difficulty Prediction Models...")
        self.stdout.write("-" * 50)
        from ml_engine.trainer import DifficultyTrainer
        trainer = DifficultyTrainer()
        difficulty_metrics = trainer.train(stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS("  ✅ Difficulty models trained and saved.\n"))

        # 2. Train Isolation Forest for cheating detection
        self.stdout.write("🔍 [2/3] Training Cheating Detection (Isolation Forest)...")
        self.stdout.write("-" * 50)
        from ml_engine.cheating import HybridCheatingDetector
        detector = HybridCheatingDetector()
        scan_result = detector.scan_all_students(stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS("  ✅ Cheating detection model trained.\n"))

        # 3. Update all question difficulty scores
        self.stdout.write("📈 [3/3] Updating question difficulty scores with ML predictions...")
        self.stdout.write("-" * 50)
        from ml_engine.models import Question
        from ml_engine.difficulty import HybridDifficultyCalculator

        calculator = HybridDifficultyCalculator()
        updated = 0
        for q in Question.objects.all():
            result = calculator.analyze(q)
            q.difficulty_score = result['difficulty_score']
            q.text_complexity = result['text_complexity']
            q.bloom_level = result['bloom_level']
            q.save(update_fields=['difficulty_score', 'text_complexity', 'bloom_level'])
            updated += 1

        self.stdout.write(f"  Updated {updated} questions with ML-predicted difficulty scores.")
        self.stdout.write(self.style.SUCCESS("  ✅ Question scores updated.\n"))

        # Summary
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.SUCCESS("  ALL MODELS TRAINED SUCCESSFULLY"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))

        if 'random_forest' in difficulty_metrics:
            rf = difficulty_metrics['random_forest']
            self.stdout.write(f"  RF  — MAE: {rf.get('mae', 'N/A')}, R²: {rf.get('r2', 'N/A')}")
        if 'xgboost' in difficulty_metrics and isinstance(difficulty_metrics['xgboost'], dict):
            xgb = difficulty_metrics['xgboost']
            if 'mae' in xgb:
                self.stdout.write(f"  XGB — MAE: {xgb['mae']}, R²: {xgb['r2']}")

        self.stdout.write(f"  Cheating scan: {scan_result.get('flagged', 0)} anomalies detected")
        self.stdout.write(f"  Questions updated: {updated}")
