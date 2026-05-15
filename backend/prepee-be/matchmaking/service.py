import json
import time
import logging
from django_redis import get_redis_connection
from .models import Match, MatchPlayer

logger = logging.getLogger(__name__)

redis = get_redis_connection("default")


def get_questions_for_user(user, category, count=10):
    """Fetch personalized questions using ML Hybrid Recommender."""
    try:
        from ml_engine.recommender import HybridRecommender
        from ml_engine.models import Question

        recommender = HybridRecommender()
        # Recommend questions for the user
        result = recommender.recommend(user, n=count)
        
        # In case we want to filter by category specifically:
        question_ids = [item['id'] for item in result['question_ids']]
        questions = list(Question.objects.filter(id__in=question_ids))

        if not questions:
            questions = list(Question.objects.order_by('?')[:count])

        return [
            {
                "id": q.id,
                "question": q.text,
                "options": q.options,
                "answer": q.correct_answer_index,
                "explanation": q.explanation,
                "category": q.subject,
                "difficulty": q.difficulty_score,
            }
            for q in questions
        ]
    except Exception as e:
        logger.warning(f"Failed to fetch ML questions: {e}")
        return None


def get_elo_range(wait_time):
    if wait_time <= 15:
        return 50
    elif wait_time <= 30:
        return 100
    elif wait_time <= 45:
        return 200
    else:
        return 400


def find_match_for_user(user, category="general"):
    redis_client = redis

    queue_key = f"match_queue:{category}"
    user_match_key = f"user_match:{user.id}"

    # 1 Check if user is already matched
    match_id = redis_client.get(user_match_key)
    if match_id:
        match_id = int(match_id)
        match = Match.objects.get(id=match_id)

        # Find opponent
        opponent = None
        players = match.matchplayer_set.all()
        for player in players:
            if player.user.username != user.username:
                opponent = player.user

        # Get questions — already a Python object from JSONField
        questions = match.questions
        if isinstance(questions, str):
            questions = json.loads(questions)

        if not questions:
            questions = get_questions_for_user(user, match.category)
            if questions:
                match.questions = questions
                match.save(update_fields=['questions'])

        return {
            "status": "matched",
            "match_id": match_id,
            "questions": questions,
            "opponentName": opponent.username if opponent else "Unknown",
            "opponentCity": opponent.city if opponent else "Unknown",
            "timeControl": match.time_control,
        }

    # 2 Check if user is already in the queue
    all_candidates_raw = redis_client.zrange(queue_key, 0, -1)
    for item in all_candidates_raw:
        cand = json.loads(item)
        if cand["user_id"] == user.id:
            return {"status": "waiting"}

    # 3 Not matched and not in queue → add user to queue
    user_data = {
        "user_id": user.id,
        "elo": user.elo,
        "username": user.username,
        "timestamp": int(time.time()),
    }

    redis_client.zadd(queue_key, {json.dumps(user_data): user.elo})
    logger.info(f"Added user {user.username} to queue {queue_key}")

    return {"status": "waiting"}
