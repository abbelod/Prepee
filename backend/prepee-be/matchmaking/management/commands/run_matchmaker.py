import time
import json
from django.core.management.base import BaseCommand
from django_redis import get_redis_connection
from matchmaking.models import Match, MatchPlayer


def get_elo_range(wait_time):
    base = 50
    extra = (wait_time // 10) * 20
    return base + extra


class Command(BaseCommand):
    help = "Runs continuous matchmaking worker"

    def handle(self, *args, **options):

        print("Matchmaking worker started...")

        redis_client = get_redis_connection("default")

        while True:
            categories = ["general", "Logical Reasoning", "Biology", "Mathematics", "Chemistry", "Physics", "ECAT", "MCAT", "English"]

            for category in categories:
                key = f"match_queue:{category}"
                all_raw = redis_client.zrange(key, 0, -1)
                print(f"People queued for {category}: {len(all_raw)}")

                for candidate_raw in all_raw:
                    cand = json.loads(candidate_raw)

                    # Skip if already matched
                    if redis_client.get(f"user_match:{cand['user_id']}"):
                        continue

                    # look for opponent
                    for opponent_raw in all_raw:
                        opp = json.loads(opponent_raw)

                        if opp["user_id"] == cand["user_id"]:
                            continue

                        wait_time = int(time.time()) - opp["timestamp"]
                        allowed_diff = get_elo_range(wait_time)

                        if abs(opp["elo"] - cand["elo"]) <= allowed_diff:

                            redis_client.zrem(key, candidate_raw)
                            redis_client.zrem(key, opponent_raw)

                            print("CREATIN GMATCH OBJECT")
                            match = Match.objects.create(category=category)
                            MatchPlayer.objects.create(match=match, user_id=cand["user_id"])
                            MatchPlayer.objects.create(match=match, user_id=opp["user_id"])

                            redis_client.set(
                                f"user_match:{cand['user_id']}", match.id, ex=3600
                            )
                            redis_client.set(
                                f"user_match:{opp['user_id']}", match.id, ex=3600
                            )

                            print(f"[{category}] Match created: {cand['user_id']} vs {opp['user_id']}")
                            break

            time.sleep(0.5)