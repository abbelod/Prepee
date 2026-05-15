from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Question, QuestionAttempt, StudentProfile, CheatingFlag

User = get_user_model()


class QuestionModelTest(TestCase):
    def setUp(self):
        self.question = Question.objects.create(
            text="What is the powerhouse of the cell?",
            options=["Nucleus", "Mitochondria", "Ribosome", "Lysosome"],
            correct_answer_index=1,
            explanation="Mitochondria is known as the powerhouse of the cell.",
            subject="Biology",
            topic="Cell Biology",
            difficulty_score=0.25,
            bloom_level="recall",
        )

    def test_correct_answer_property(self):
        self.assertEqual(self.question.correct_answer, "Mitochondria")

    def test_str_representation(self):
        self.assertIn("Biology", str(self.question))
        self.assertIn("Cell Biology", str(self.question))


class StudentProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            subject_strengths={"Physics": 0.85, "Chemistry": 0.42, "Biology": 0.71},
            accuracy_rate=0.66,
            total_questions_attempted=100,
        )

    def test_weakest_subjects(self):
        weakest = self.profile.get_weakest_subjects(2)
        self.assertEqual(weakest[0], "Chemistry")

    def test_strongest_subjects(self):
        strongest = self.profile.get_strongest_subjects(1)
        self.assertEqual(strongest[0], "Physics")
