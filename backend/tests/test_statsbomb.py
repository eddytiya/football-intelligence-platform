import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.statsbomb_client import StatsBombClient


def main():

    client = StatsBombClient()

    print("=" * 60)
    print("COMPETITIONS")
    print("=" * 60)

    competitions = client.get_competitions()

    print(f"Total competitions : {len(competitions)}")

    competition = competitions[0]

    print(competition)

    print()

    competition_id = competition["competition_id"]
    season_id = competition["season_id"]

    print("=" * 60)
    print("MATCHES")
    print("=" * 60)

    matches = client.get_matches(
        competition_id,
        season_id
    )

    print(f"Total matches : {len(matches)}")

    first_match = matches[0]

    print(first_match)

    match_id = first_match["match_id"]

    print()

    print("=" * 60)
    print("LINEUPS")
    print("=" * 60)

    lineup = client.get_lineup(match_id)

    print(f"Teams in lineup : {len(lineup)}")

    print(lineup[0]["team_name"])

    print()

    print("=" * 60)
    print("EVENTS")
    print("=" * 60)

    events = client.get_events(match_id)

    print(f"Events : {len(events)}")

    print(events[0]["type"]["name"])

    print()

    print("=" * 60)
    print("360 DATA")
    print("=" * 60)

    try:

        data360 = client.get_three_sixty(match_id)

        print(f"Frames : {len(data360)}")

    except FileNotFoundError:

        print("360 data not available for this match.")


if __name__ == "__main__":
    main()