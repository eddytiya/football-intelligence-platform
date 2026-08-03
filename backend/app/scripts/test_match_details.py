import json

from app.services.football_api import FootballAPIClient


def main():
    client = FootballAPIClient()

    match_id = 554760

    print(f"\nFetching Match {match_id}...\n")

    data = client.get(f"/matches/{match_id}")

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