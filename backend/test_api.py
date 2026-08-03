from app.services.football_api import FootballAPIClient


def main():
    client = FootballAPIClient()

    data = client.get("/competitions")

    print("=" * 60)
    print("FOOTBALL-DATA API TEST")
    print("=" * 60)

    print(f"Total Competitions: {data['count']}")
    print()

    print("First 10 Competitions:\n")

    for competition in data["competitions"][:10]:
        print(
            f"{competition['id']:>3} | "
            f"{competition['code']:<6} | "
            f"{competition['name']}"
        )


if __name__ == "__main__":
    main()