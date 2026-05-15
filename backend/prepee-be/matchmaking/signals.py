import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Match

logger = logging.getLogger(__name__)


def get_questions_for_category(category, count=10):
    """Fetch real questions from ml_engine Question model."""
    try:
        from ml_engine.models import Question

        questions = Question.objects.filter(subject=category)
        if not questions.exists():
            questions = Question.objects.all()
        if not questions.exists():
            return None

        question_list = list(questions.order_by('?')[:count])
        return [
            {
                "id": q.id,
                "question": q.text,
                "options": q.options,
                "answer": q.correct_answer_index,
                "explanation": q.explanation,
                "category": q.subject,
            }
            for q in question_list
        ]
    except Exception as e:
        logger.warning(f"Failed to fetch questions for category '{category}': {e}")
        return None


@receiver(post_save, sender=Match)
def add_quiz_to_match(sender, instance, created, **kwargs):
    if not created:
        return

    questions = get_questions_for_category(instance.category)
    if questions:
        instance.questions = questions
        instance.save(update_fields=['questions'])
        logger.info(f"Assigned {len(questions)} questions to Match {instance.id}")
