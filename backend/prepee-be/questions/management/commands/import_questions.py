import json
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from questions.models import Questions  # replace 'yourapp' with your actual app name

class Command(BaseCommand):
    help = 'Import questions from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        file_path = options['json_file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR('Invalid JSON format'))
            return

        # Expecting a list of question objects
        if not isinstance(data, list):
            self.stderr.write(self.style.ERROR('JSON root must be an array of questions'))
            return

        created_count = 0
        updated_count = 0
        errors = []

        for idx, item in enumerate(data):
            # Map JSON fields to model fields (customise as needed)
            subject = item.get('subject')
            text = item.get('text') or item.get('question')   # allow both keys
            explanation = item.get('explanation', '')
            option_a = item.get('option_a')
            option_b = item.get('option_b')
            option_c = item.get('option_c')
            option_d = item.get('option_d')
            correct_option = item.get('correct_option')  # expected 'A','B','C','D'

            # If your JSON uses a different structure, adjust here
            # For example, if you have "options": ["opt1","opt2","opt3","opt4"] and "answer":0
            if 'options' in item and isinstance(item['options'], list):
                opts = item['options']
                if len(opts) >= 4:
                    option_a, option_b, option_c, option_d = opts[0], opts[1], opts[2], opts[3]
                if 'answer' in item:
                    # answer is 0‑based index -> convert to letter
                    answer_index = item['answer']
                    correct_option = ['A','B','C','D'][answer_index] if 0 <= answer_index <= 3 else None

            # Basic validation
            if not all([subject, text, option_a, option_b, option_c, option_d, correct_option]):
                errors.append(f"Row {idx}: missing required fields")
                continue
            if correct_option not in ['A','B','C','D']:
                errors.append(f"Row {idx}: correct_option must be A, B, C, or D")
                continue

            # Use update_or_create to avoid duplicates (identify by subject + text? or by a unique id)
            # If your JSON has an "id" field, you could use that as identifier.
            # Here we assume no duplicate question text within the same subject.
            question, created = Questions.objects.update_or_create(
                subject=subject,
                text=text,
                defaults={
                    'explanation': explanation,
                    'option_a': option_a,
                    'option_b': option_b,
                    'option_c': option_c,
                    'option_d': option_d,
                    'correct_option': correct_option,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # Print summary
        self.stdout.write(self.style.SUCCESS(f'Done. Created: {created_count}, Updated: {updated_count}'))
        if errors:
            self.stderr.write(self.style.WARNING('Errors encountered:'))
            for err in errors:
                self.stderr.write(f'  {err}')