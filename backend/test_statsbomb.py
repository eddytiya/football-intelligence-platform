from app.services.statsbomb_client import StatsBombClient


def main():
    client = StatsBombClient()

    competitions = client.get_competitions()

    print("=" * 60)
    print(f"Total competitions : {len(competitions)}")
    print("=" * 60)

    print(competitions[0])


if __name__ == "__main__":
    main()