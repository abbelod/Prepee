import json
from django.core.management.base import BaseCommand
from ml_engine.evaluator import ModelEvaluator


class Command(BaseCommand):
    help = "Generate comprehensive ML model evaluation report"

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true', help='Output as JSON')
        parser.add_argument('--save', type=str, help='Save report to file')

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(self.style.MIGRATE_HEADING("  PREPEE ML EVALUATION REPORT"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))

        evaluator = ModelEvaluator()
        report = evaluator.generate_report()

        if options.get('json'):
            self.stdout.write(json.dumps(report, indent=2, default=str))
        else:
            self._print_report(report)

        if options.get('save'):
            with open(options['save'], 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(f"\nReport saved to {options['save']}"))

    def _print_report(self, report):
        # Dataset info
        ds = report.get('dataset_info', {})
        self.stdout.write(f"\n📊 Dataset Summary")
        self.stdout.write(f"   Questions: {ds.get('total_questions', 0)}")
        self.stdout.write(f"   Attempts: {ds.get('total_attempts', 0)}")
        self.stdout.write(f"   Students: {ds.get('total_students', 0)}")
        self.stdout.write(f"   Data Type: {ds.get('data_type', 'Unknown')}")

        # Difficulty prediction
        dp = report.get('difficulty_prediction', {})
        self.stdout.write(f"\n📈 1. Difficulty Prediction")
        self.stdout.write(f"   Model: {dp.get('model_type', 'N/A')}")
        if 'metrics' in dp:
            m = dp['metrics']
            self.stdout.write(f"   MAE: {m.get('mae', 'N/A')}")
            self.stdout.write(f"   RMSE: {m.get('rmse', 'N/A')}")
            self.stdout.write(f"   R² Score: {m.get('r2_score', 'N/A')}")
            self.stdout.write(f"   Binned Accuracy: {m.get('binned_accuracy', 'N/A')}")

        # Recommendations
        rec = report.get('recommendation_engine', {})
        self.stdout.write(f"\n🎯 2. Recommendation Engine")
        self.stdout.write(f"   Model: {rec.get('model_type', 'N/A')}")
        if 'metrics' in rec:
            m = rec['metrics']
            self.stdout.write(f"   Weakness Targeting: {m.get('weakness_targeting_rate', 'N/A')}")
            self.stdout.write(f"   Coverage: {m.get('avg_recommendation_coverage', 'N/A')}")

        # Cheating detection
        cd = report.get('cheating_detection', {})
        self.stdout.write(f"\n🔍 3. Cheating Detection")
        self.stdout.write(f"   Model: {cd.get('model_type', 'N/A')}")
        if 'metrics' in cd:
            m = cd['metrics']
            self.stdout.write(f"   Detection Rate: {m.get('detection_rate', 'N/A')}")
            self.stdout.write(f"   False Positive Estimate: {m.get('false_positive_estimate', 'N/A')}")
            self.stdout.write(f"   Total Flags: {m.get('total_flags_generated', 0)}")

        self.stdout.write(self.style.SUCCESS("\n✅ Evaluation complete."))
