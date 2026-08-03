from app.db.session import SessionLocal
from app.repositories.match_repository import MatchRepository


def main():

    db = SessionLocal()

    try:
        repository = MatchRepository(db)

        matches = repository.get_finished_matches()

        print(f"\nFinished Matches: {len(matches)}")

        print("\nFirst Match\n")

        first_match = matches[0]

        print(f"ID: {first_match.id}")
        print(f"Date: {first_match.utc_date}")
        print(f"Home Team: {first_match.home_team_id}")
        print(f"Away Team: {first_match.away_team_id}")
        print(f"Score: {first_match.home_score}-{first_match.away_score}")

    finally:
        db.close()


if __name__ == "__main__":
    main()