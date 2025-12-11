import json
import time
from django_redis import get_redis_connection
from .models import Match, MatchPlayer
# from django.contrib.auth.models import User
# from .utils import generate_questions

SAMPLE_QUESTIONS = [
    {
        "id": 1,
        "question": "What is the capital of France?",
        "options": ["London", "Paris", "Berlin", "Rome"],
        "answer": 1,
        "explanation": "Paris is the capital of France."
    },
    {
        "id": 2,
        "question": "What is 2 + 2?",
        "options": ["3", "4", "5", "6"],
        "answer": 1,
        "explanation": "2 + 2 equals 4."
    },
    {
        "id": 3,
        "question": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Venus", "Jupiter"],
        "answer": 1,
        "explanation": "Mars is called the Red Planet due to its reddish appearance."
    },
    {
        "id": 4,
        "question": "Who wrote 'Romeo and Juliet'?",
        "options": ["Charles Dickens", "William Shakespeare", "Mark Twain", "Jane Austen"],
        "answer": 1,
        "explanation": "William Shakespeare wrote 'Romeo and Juliet'."
    },
    {
        "id": 5,
        "question": "What is the boiling point of water at sea level?",
        "options": ["90°C", "100°C", "110°C", "120°C"],
        "answer": 1,
        "explanation": "Water boils at 100°C at sea level."
    },
    {
        "id": 6,
        "question": "Which gas do humans breathe in for survival?",
        "options": ["Carbon dioxide", "Oxygen", "Nitrogen", "Hydrogen"],
        "answer": 1,
        "explanation": "Humans need oxygen to survive."
    },
    {
        "id": 7,
        "question": "What is the largest mammal on Earth?",
        "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"],
        "answer": 1,
        "explanation": "The Blue Whale is the largest mammal."
    },
    {
        "id": 8,
        "question": "Which element has the chemical symbol 'O'?",
        "options": ["Oxygen", "Gold", "Osmium", "Silver"],
        "answer": 0,
        "explanation": "The symbol 'O' stands for Oxygen."
    },
    {
        "id": 9,
        "question": "What is the square root of 64?",
        "options": ["6", "7", "8", "9"],
        "answer": 2,
        "explanation": "8 × 8 = 64, so the square root is 8."
    },
    {
        "id": 10,
        "question": "Which continent is Australia in?",
        "options": ["Africa", "Europe", "Australia", "Asia"],
        "answer": 2,
        "explanation": "Australia is its own continent."
    }
]

redis = get_redis_connection("default")

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
    print(queue_key)
    user_match_key = f"user_match:{user.id}"

    all_candidates_raw = redis_client.zrange(queue_key, 0, -1)
    print(all_candidates_raw)

    # 1 Check if user is already matched by the matchmaker job
    match_id = redis_client.get(user_match_key)
    if match_id:
        redis_client.delete(user_match_key) # Remove because it is no longer needed
        print("User already matched")
        match_id = int(match_id)
        match = Match.objects.get(id=match_id)

        players = match.matchplayer_set.all()
        for player in players:
            print(player.user.username)
            if player.user.username != user.username:
                opponent = player.user
                print(opponent.city)
                print(opponent.username)


        return {
            "status": "matched",
            "match_id": match_id,
            "questions": match.questions,
            "opponentName": opponent.username,
            "opponentCity": opponent.city,
            "timeControl": match.time_control
        }

    # 2 Check if user is already in the queue
    all_candidates_raw = redis_client.zrange(queue_key, 0, -1)
    for item in all_candidates_raw:
        cand = json.loads(item)
        if cand["user_id"] == user.id:
            print("User already in waiting queue")
            return {"status": "waiting"}

    # 3 Not matched and not in queue → add user to queue
    user_data = {
        "user_id": user.id,
        "elo": user.elo,
        "username": user.username,
        "timestamp": int(time.time())
    }

    redis_client.zadd(queue_key, {json.dumps(user_data): user.elo})
    print("Added user to queue")

    return {"status": "waiting"}