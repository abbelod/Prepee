from rest_framework import serializers
from .models import Question, QuestionAttempt, StudentProfile, CheatingFlag


class QuestionSerializer(serializers.ModelSerializer):
    correct_answer = serializers.ReadOnlyField()

    class Meta:
        model = Question
        fields = [
            'id', 'text', 'options', 'correct_answer_index', 'correct_answer',
            'explanation', 'subject', 'topic', 'difficulty_score',
            'text_complexity', 'bloom_level', 'created_at'
        ]


class QuestionDifficultySerializer(serializers.Serializer):
    """For the /ml/difficulty/analyze/ endpoint — ad-hoc text analysis."""
    text = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField(), required=False)
    subject = serializers.CharField(required=False, default='general')
    topic = serializers.CharField(required=False, default='general')


class DifficultyResultSerializer(serializers.Serializer):
    difficulty_score = serializers.FloatField()
    text_complexity = serializers.FloatField()
    bloom_level = serializers.CharField()
    subject_adjustment = serializers.FloatField()
    option_similarity = serializers.FloatField()
    breakdown = serializers.DictField()


class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    elo = serializers.IntegerField(source='user.elo', read_only=True)
    weakest_subjects = serializers.SerializerMethodField()
    strongest_subjects = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            'username', 'email', 'elo',
            'subject_strengths', 'topic_strengths',
            'avg_time_per_question', 'total_questions_attempted',
            'accuracy_rate', 'weakest_subjects', 'strongest_subjects',
            'updated_at'
        ]

    def get_weakest_subjects(self, obj):
        return obj.get_weakest_subjects(3)

    def get_strongest_subjects(self, obj):
        return obj.get_strongest_subjects(3)


class QuestionRecommendationSerializer(serializers.Serializer):
    questions = QuestionSerializer(many=True)
    strategy_used = serializers.CharField()
    student_weaknesses = serializers.ListField(child=serializers.CharField())


class CheatingFlagSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = CheatingFlag
        fields = [
            'id', 'username', 'user', 'match', 'flag_type',
            'severity', 'details', 'reviewed', 'created_at'
        ]


class EvaluationReportSerializer(serializers.Serializer):
    difficulty_prediction = serializers.DictField()
    recommendation_engine = serializers.DictField()
    cheating_detection = serializers.DictField()
    dataset_info = serializers.DictField()
