import json
from pathlib import Path
from typing import Any


class StatsBombClient:
    """
    Client responsible for reading StatsBomb Open Data
    from the local filesystem.
    """

    def __init__(self):
        # backend/data/statsbomb/data
        self.base_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "statsbomb"
            / "data"
        )

    def _read_json(self, path: Path) -> Any:
        """
        Read a JSON file.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    # ---------------------------------------------------------
    # Competitions
    # ---------------------------------------------------------

    def get_competitions(self):
        return self._read_json(
            self.base_path / "competitions.json"
        )

    # ---------------------------------------------------------
    # Matches
    # ---------------------------------------------------------

    def get_matches(self, competition_id: int, season_id: int):
        file_path = (
            self.base_path
            / "matches"
            / str(competition_id)
            / f"{season_id}.json"
        )

        return self._read_json(file_path)

    # ---------------------------------------------------------
    # Lineups
    # ---------------------------------------------------------

    def get_lineup(self, match_id: int):
        file_path = (
            self.base_path
            / "lineups"
            / f"{match_id}.json"
        )

        return self._read_json(file_path)

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------

    def get_events(self, match_id: int):
        file_path = (
            self.base_path
            / "events"
            / f"{match_id}.json"
        )

        return self._read_json(file_path)

    # ---------------------------------------------------------
    # StatsBomb 360
    # ---------------------------------------------------------

    def get_three_sixty(self, match_id: int):
        file_path = (
            self.base_path
            / "three-sixty"
            / f"{match_id}.json"
        )

        return self._read_json(file_path)