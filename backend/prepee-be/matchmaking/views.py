import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_redis import get_redis_connection
from .service import find_match_for_user
from .models import Match, MatchPlayer

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# HELPER: Create QuestionAttempt records
# ─────────────────────────────────────────────

def _create_question_attempts(user, match, submission, questions, total_time):
    """Create ml_engine QuestionAttempt records from a player's submission."""
    try:
        from ml_engine.models import Question, QuestionAttempt

        num_questions = len(questions) if questions else 0
        avg_time = total_time / num_questions if num_questions > 0 else 0

        attempts = []
        for q in questions:
            qid = q["id"]
            correct_ans = q["options"][q["answer"]]
            selected = submission.get(str(qid))

            if selected is None:
                continue

            try:
                question_obj = Question.objects.get(id=qid)
            except Question.DoesNotExist:
                continue

            attempts.append(QuestionAttempt(
                student=user,
                question=question_obj,
                match=match,
                selected_answer=selected,
                is_correct=(selected == correct_ans),
                time_taken_seconds=round(avg_time, 2),
            ))

        if attempts:
            QuestionAttempt.objects.bulk_create(attempts)
            logger.info(f"Created {len(attempts)} QuestionAttempts for {user.username} in Match {match.id}")

    except Exception as e:
        logger.warning(f"Failed to create QuestionAttempts: {e}")


# ─────────────────────────────────────────────
# HELPER: Post-match ML processing
# ─────────────────────────────────────────────

def _run_post_match_ml(user, match):
    """Run cheating detection and update student profile after match."""
    try:
        from ml_engine.cheating import HybridCheatingDetector
        from ml_engine.recommender import StudentProfiler

        # Cheating detection
        detector = HybridCheatingDetector()
        result = detector.analyze_match(user, match)
        if result and result.get('should_flag'):
            logger.warning(
                f"Cheating flag for {user.username} in Match {match.id}: "
                f"score={result['composite_score']:.4f}, signal={result['dominant_signal']}"
            )

        # Update student profile
        profiler = StudentProfiler()
        profiler.update_profile(user)

    except Exception as e:
        logger.warning(f"Post-match ML processing failed for {user.username}: {e}")


# ─────────────────────────────────────────────
# HELPER: Safely read match questions from JSONField
# ─────────────────────────────────────────────

def _get_match_questions(match):
    """Safely get questions, handling both JSON string and native JSONField."""
    import json
    q = match.questions
    if isinstance(q, str):
        return json.loads(q)
    return q


# ─────────────────────────────────────────────
# VIEWS
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def find_match(request):
    user = request.user
    category = request.data.get("category", "general")
    result = find_match_for_user(user, category)
    return Response(result)


@api_view(['GET'])
def clear_matchmaking_queues(request, categories=None, clear_user_matches=True):
    """Clears all matchmaking queues in Redis."""
    if categories is None:
        categories = [
            "general", "Logical Reasoning", "Biology", "Mathematics",
            "Chemistry", "Physics", "ECAT", "MCAT", "English",
        ]

    redis_client = get_redis_connection("default")

    for category in categories:
        queue_key = f"match_queue:{category}"
        redis_client.delete(queue_key)

    if clear_user_matches:
        for key in redis_client.scan_iter("user_match:*"):
            redis_client.delete(key)

    return Response({"success"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_quiz_submission(request, match_id):

    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        return Response({"error": "Match not found"}, status=404)

    # Get current player's MatchPlayer
    try:
        mp = MatchPlayer.objects.get(match=match, user=request.user)
    except MatchPlayer.DoesNotExist:
        return Response({"error": "You are not part of this match"}, status=403)

    # Get questions from match (handles both JSON string and native JSONField)
    correct_answers = _get_match_questions(match)

    # If user has not submitted answers yet, submit them.
    if not mp.submitted:
        submission = request.data.get("submission")
        time_taken = request.data.get("time_taken", 0)

        if not submission:
            return Response({"error": "Submission missing"}, status=400)

        mp.submission = submission
        mp.time_taken = float(time_taken)
        mp.submitted = True

        def calculate_score(submission_dict):
            score = 0
            for q in correct_answers:
                qid = q["id"]
                correct_ans = q["options"][q["answer"]]
                if str(qid) in submission_dict and submission_dict[str(qid)] == correct_ans:
                    score += 1
            return score

        mp.score = calculate_score(mp.submission)
        mp.save()

        # Create QuestionAttempt records for ML tracking
        _create_question_attempts(
            user=request.user,
            match=match,
            submission=mp.submission,
            questions=correct_answers,
            total_time=mp.time_taken,
        )

    # Get opponent MatchPlayer
    opponent = MatchPlayer.objects.filter(match=match).exclude(user=request.user).first()

    if not opponent:
        return Response({"error": "Opponent not found"}, status=500)

    # If opponent has NOT submitted yet → tell player to wait
    if not opponent.submitted:
        return Response({"status": "waiting", "message": "Waiting for opponent..."})

    # Both submitted → determine winner
    if mp.score > opponent.score:
        mp.is_winner = True
        opponent.is_winner = False
    elif opponent.score > mp.score:
        mp.is_winner = False
        opponent.is_winner = True
    else:
        # Tie → decide by faster time
        if mp.time_taken < opponent.time_taken:
            mp.is_winner = True
            opponent.is_winner = False
        elif opponent.time_taken < mp.time_taken:
            mp.is_winner = False
            opponent.is_winner = True
        else:
            mp.is_winner = False
            opponent.is_winner = False

    mp.save()
    opponent.save()

    # Mark match complete
    match.is_completed = True
    match.save()

    # Run cheating detection + update ML profiles for both players
    _run_post_match_ml(request.user, match)
    _run_post_match_ml(opponent.user, match)

    # Return result to frontend
    return Response({
        "status": "completed",
        "your_score": mp.score,
        "opponent_score": opponent.score,
        "winner": mp.user.username if mp.is_winner else opponent.user.username,
        "you_won": mp.is_winner,
        "answers": correct_answers,
    })
