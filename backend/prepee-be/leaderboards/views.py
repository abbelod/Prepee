from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
User = get_user_model()


@api_view(['GET'])
def leaderboard_api(request):
    users = User.objects.all().order_by('-elo')
    for user in users:
        print(user.elo)
    leaderboard = [
        {
            "position": idx + 1,
            "username": u.username,
            "city": getattr(u, "city", ""),
            "elo": u.elo
        }
        for idx, u in enumerate(users)
    ]
    return Response(leaderboard)