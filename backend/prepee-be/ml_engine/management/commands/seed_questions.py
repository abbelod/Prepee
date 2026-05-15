import json
from django.core.management.base import BaseCommand
from ml_engine.models import Question


class Command(BaseCommand):
    help = "Seed 300+ quiz questions across 8 categories into the database"

    def handle(self, *args, **options):
        if Question.objects.exists():
            self.stdout.write(self.style.WARNING(
                f"Database already has {Question.objects.count()} questions. "
                "Use --flush to clear and re-seed."
            ))
            if '--flush' not in args:
                return

        if '--flush' in args:
            Question.objects.all().delete()
            self.stdout.write("Cleared existing questions.")

        from ml_engine.question_bank import QUESTION_BANK
        count = 0
        for q in QUESTION_BANK:
            Question.objects.create(
                text=q['text'],
                options=q['options'],
                correct_answer_index=q['correct'],
                explanation=q.get('explanation', ''),
                subject=q['subject'],
                topic=q['topic'],
                bloom_level=q.get('bloom', 'recall'),
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} questions!"))

        # Print summary by subject
        subjects = Question.objects.values_list('subject', flat=True).distinct()
        for subj in sorted(subjects):
            n = Question.objects.filter(subject=subj).count()
            self.stdout.write(f"  {subj}: {n} questions")
