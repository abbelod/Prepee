from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .models import Question, StudentProfile, CheatingFlag
from .serializers import (
    QuestionSerializer,
    QuestionDifficultySerializer,
    DifficultyResultSerializer,
    StudentProfileSerializer,
    QuestionRecommendationSerializer,
    CheatingFlagSerializer,
    EvaluationReportSerializer,
)


# ─────────────────────────────────────────────
# DIFFICULTY PREDICTION ENDPOINTS
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question_difficulty(request, question_id):
    """Get difficulty score for a specific question."""
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)

    # Import here to avoid circular imports
    from .difficulty import HybridDifficultyCalculator

    calculator = HybridDifficultyCalculator()
    result = calculator.analyze(question)

    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_difficulty(request):
    """Analyze difficulty of ad-hoc question text."""
    serializer = QuestionDifficultySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    from .difficulty import HybridDifficultyCalculator

    calculator = HybridDifficultyCalculator()
    result = calculator.analyze_text(
        text=serializer.validated_data['text'],
        options=serializer.validated_data.get('options', []),
        subject=serializer.validated_data.get('subject', 'general'),
        topic=serializer.validated_data.get('topic', 'general'),
    )

    return Response(result)


# ─────────────────────────────────────────────
# RECOMMENDATION ENGINE ENDPOINTS
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """Get recommended questions for the current user."""
    from .recommender import HybridRecommender

    recommender = HybridRecommender()
    result = recommender.recommend(request.user, n=10)

    questions = Question.objects.filter(id__in=[q['id'] for q in result['question_ids']])
    serializer = QuestionSerializer(questions, many=True)

    return Response({
        'questions': serializer.data,
        'strategy_used': result['strategy'],
        'student_weaknesses': result.get('weaknesses', []),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_practice_set(request):
    """Get a practice set of 10 questions targeting weak areas."""
    from .recommender import HybridRecommender

    recommender = HybridRecommender()
    result = recommender.get_practice_set(request.user, n=10)

    questions = Question.objects.filter(id__in=result['question_ids'])
    serializer = QuestionSerializer(questions, many=True)

    return Response({
        'questions': serializer.data,
        'focus_areas': result.get('focus_areas', []),
        'difficulty_range': result.get('difficulty_range', {}),
    })


# ─────────────────────────────────────────────
# STUDENT PROFILE ENDPOINT
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_profile(request):
    """Get the current user's ML profile (strengths/weaknesses)."""
    profile, created = StudentProfile.objects.get_or_create(user=request.user)

    if created:
        # First time — update from existing attempts
        from .recommender import StudentProfiler
        StudentProfiler().update_profile(request.user)
        profile.refresh_from_db()

    serializer = StudentProfileSerializer(profile)
    return Response(serializer.data)


# ─────────────────────────────────────────────
# CHEATING DETECTION ENDPOINTS (Admin only)
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_cheating_flags(request):
    """List all cheating flags (admin only)."""
    reviewed = request.query_params.get('reviewed', None)
    min_severity = request.query_params.get('min_severity', None)

    flags = CheatingFlag.objects.all()

    if reviewed is not None:
        flags = flags.filter(reviewed=reviewed.lower() == 'true')
    if min_severity is not None:
        flags = flags.filter(severity__gte=float(min_severity))

    serializer = CheatingFlagSerializer(flags[:100], many=True)
    return Response({
        'count': flags.count(),
        'flags': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_cheating_flags(request, user_id):
    """Get cheating flags for a specific user (admin only)."""
    flags = CheatingFlag.objects.filter(user_id=user_id)
    serializer = CheatingFlagSerializer(flags, many=True)
    return Response({
        'user_id': user_id,
        'total_flags': flags.count(),
        'unreviewed': flags.filter(reviewed=False).count(),
        'flags': serializer.data,
    })


# ─────────────────────────────────────────────
# EVALUATION REPORT ENDPOINT (Admin only)
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def evaluation_report(request):
    """Get full ML model evaluation report (admin only)."""
    from .evaluator import ModelEvaluator

    evaluator = ModelEvaluator()
    report = evaluator.generate_report()

    return Response(report)
