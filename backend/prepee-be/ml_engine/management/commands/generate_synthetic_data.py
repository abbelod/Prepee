from django.core.management.base import BaseCommand
from ml_engine.data_generator import SyntheticDataGenerator


class Command(BaseCommand):
    help = "Generate synthetic student data for ML model training"

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=500, help='Number of students')
        parser.add_argument('--attempts', type=int, default=50000, help='Number of attempts')
        parser.add_argument('--cheater-ratio', type=float, default=0.03, help='Ratio of cheaters')
        parser.add_argument('--flush', action='store_true', help='Clear existing data first')

    def handle(self, *args, **options):
        if options['flush']:
            from ml_engine.models import QuestionAttempt, StudentProfile, CheatingFlag
            from django.contrib.auth import get_user_model
            User = get_user_model()

            self.stdout.write("Flushing existing synthetic data...")
            CheatingFlag.objects.all().delete()
            QuestionAttempt.objects.all().delete()
            StudentProfile.objects.all().delete()
            User.objects.filter(email__endswith='@prepee.synthetic').delete()
            self.stdout.write(self.style.SUCCESS("Flushed."))

        generator = SyntheticDataGenerator(
            num_students=options['students'],
            num_attempts=options['attempts'],
            cheater_ratio=options['cheater_ratio'],
        )

        result = generator.generate_all(stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Generation complete!\n"
            f"   Students: {result['students']}\n"
            f"   Attempts: {result['attempts']}\n"
            f"   Cheaters: {result['cheaters']}\n"
            f"   Questions: {result['questions']}\n"
        ))
