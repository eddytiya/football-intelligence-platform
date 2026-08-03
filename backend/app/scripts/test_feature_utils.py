from datetime import datetime

from app.db.session import SessionLocal
from app.services.feature_engineering.feature_utils import (
    calculate_points,
    get_previous_matches,
)


def main():
    db = SessionLocal()

    team_id = 95

    matches = get_previous_matches(
        db=db,
        team_id=team_id,
        before_date=datetime(2025, 1, 1),
        limit=5,
    )

    print("\nPrevious Matches\n")

    for match in matches:
        print(
            f"{match.utc_date} | "
            f"{match.home_team_id} "
            f"{match.home_score}-{match.away_score} "
            f"{match.away_team_id}"
        )

    points = calculate_points(matches, team_id)

    print(f"\nPoints in last {len(matches)} matches: {points}")

    db.close()


if __name__ == "__main__":
    main()