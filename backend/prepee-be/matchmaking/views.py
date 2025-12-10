from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .service import find_match_for_user
from django_redis import get_redis_connection
from .models import Match, MatchPlayer
import json

# Create your views here.

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def find_match(request):
    user = request.user
    category = request.data.get("category", "general")

    result = find_match_for_user(user, category)

    return Response(result)


@api_view(['GET'])
def clear_matchmaking_queues(request, categories=None, clear_user_matches=True):
    """
    Clears all matchmaking queues in Redis.
    
    categories: list of category names to clear. Defaults to ["general", "math", "science"]
    clear_user_matches: if True, also clears user_match keys
    """
    if categories is None:
        categories = ["general", "Logical Reasoning", "Biology", "Mathematics", "Chemistry", "Physics", "ECAT", "MCAT", "English"]


    redis_client = get_redis_connection("default")

    # Clear all category queues
    for category in categories:
        queue_key = f"match_queue:{category}"
        redis_client.delete(queue_key)
        print(f"Cleared queue: {queue_key}")

    if clear_user_matches:
        # Optional: clear all user_match keys
        # Warning: you need to know user_ids or pattern
        for key in redis_client.scan_iter("user_match:*"):
            redis_client.delete(key)
            print(f"Cleared: {key.decode('utf-8')}")

    print("cleared all queues")
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

    # If user has not submitted answers yet, submit them.
    if mp.submitted == False or True:
        # 1. Save player's submission
        submission = request.data.get("submission")
        time_taken = request.data.get("time_taken", 0)

        if not submission:
            return Response({"error": "Submission missing"}, status=400)

        mp.submission = submission
        mp.time_taken = float(time_taken)
        mp.submitted = True

        correct_answers = json.loads(match.questions)  # stored as JSON in Match model
        def calculate_score(submission_dict):
            """
            submission_dict: { question_id: selected_option_index }
            """
            score = 0
            for q in correct_answers:
                qid = q["id"]
                correct_ans = q["options"][q["answer"]]
                print("correct ans", correct_ans)
                print(type(submission_dict))
                print((submission_dict))
                print(qid)
                if str(qid) in submission_dict and submission_dict[str(qid)] == correct_ans:
                    print("correct ans")
                    score += 1
            return score

        mp.score = calculate_score(mp.submission)
        mp.save()
        print(f"{request.user.username} submitted answers: {submission} score:{mp.score}")

    # If already submitted, check for opponents submission status 

    # 2. Get opponent MatchPlayer
    opponent = MatchPlayer.objects.filter(match=match).exclude(user=request.user).first()

    if not opponent:
        return Response({"error": "Opponent not found"}, status=500)

    # If opponent has NOT submitted yet → tell player to wait
    if not opponent.submitted:
        return Response({"status": "waiting", "message": "Waiting for opponent..."})

    # 3. If both submitted → calculate results

    

    # 4. Decide winner
    if mp.score > opponent.score:
        mp.is_winner = True
        opponent.is_winner = False
    elif opponent.score > mp.score:
        mp.is_winner = False
        opponent.is_winner = True
    else:
        # tie → decide by faster time
        if mp.time_taken < opponent.time_taken:
            mp.is_winner = True
            opponent.is_winner = False
        elif opponent.time_taken < mp.time_taken:
            mp.is_winner = False
            opponent.is_winner = True
        else:
            # Complete tie
            mp.is_winner = False
            opponent.is_winner = False

    mp.save()
    opponent.save()

    # 5. Mark match complete
    match.is_completed = True
    match.save()

    # 6. Optional ELO update
    # update_elo(mp, opponent)

    # 7. Return result to frontend
    return Response({
        "status": "completed",
        "your_score": mp.score,
        "opponent_score": opponent.score,
        "winner": mp.user.username if mp.is_winner else opponent.user.username,
        "you_won": mp.is_winner,
        "answers": correct_answers
    })