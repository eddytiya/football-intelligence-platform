import json

from app.services.football_api import FootballAPIClient


def main():
    client = FootballAPIClient()

    team_id = 1768

    print(f"\nFetching Team {team_id}...\n")

    data = client.get(f"/teams/{team_id}")

    if not data:
        print("No data returned.")
        return

    print("=" * 80)
    print("TOP LEVEL KEYS")
    print("=" * 80)

    print(data.keys())

    print("\n")

    print("=" * 80)
    print("FULL RESPONSE")
    print("=" * 80)

    print(json.dumps(data, indent=4))


if __name__ == "__main__":
    main()