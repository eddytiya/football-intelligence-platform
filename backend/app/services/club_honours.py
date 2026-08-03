"""Curated, first-team honours for the clubs and national teams tracked in phase one.

The live football providers do not expose a dependable all-time honours catalogue.
These records are therefore intentionally separate from live data, carry a source
description, and use a narrow definition: senior league/cup/continental/world
honours. Super cups are displayed independently and are not inflated into the
major-honours total.
"""

from __future__ import annotations

from datetime import date
import re


def _record(kind, league=0, cups=0, super_cups=0, continental=0, world=0, source="Official club honours pages and UEFA/FIFA competition records"):
    return {
        "kind": kind,
        "league_titles": league,
        "domestic_cups": cups,
        "super_cups": super_cups,
        "continental_titles": continental,
        "world_titles": world,
        "major_honours": league + cups + continental + world,
        "recorded_honours": league + cups + super_cups + continental + world,
        "source": source,
        "verified_on": date.today().isoformat(),
        "definition": "Senior first-team honours. Domestic super cups are shown separately and excluded from major honours.",
    }


HONOURS = {
    "arsenal": _record("club", 13, 14, 2, 1),
    "manchester city": _record("club", 10, 7, 8, 3, 1),
    "manchester united": _record("club", 20, 13, 6, 6, 2),
    "liverpool": _record("club", 19, 8, 10, 13, 1),
    "chelsea": _record("club", 6, 8, 5, 9, 2),
    "tottenham": _record("club", 2, 8, 4, 4),
    "aston villa": _record("club", 7, 7, 5, 2),
    "barcelona": _record("club", 28, 32, 15, 14, 3),
    "real madrid": _record("club", 36, 20, 13, 23, 9),
    "atletico madrid": _record("club", 11, 10, 2, 8),
    "bayern munich": _record("club", 33, 20, 10, 10, 4),
    "borussia dortmund": _record("club", 8, 5, 6, 3, 1),
    "ajax": _record("club", 36, 20, 9, 9, 2),
    "paris saint germain": _record("club", 13, 16, 13, 1),
    "juventus": _record("club", 36, 15, 9, 9, 2),
    "internazionale": _record("club", 20, 9, 8, 6, 3),
    "ac milan": _record("club", 19, 5, 8, 15, 3),
    "napoli": _record("club", 4, 6, 2, 1),
    "roma": _record("club", 3, 9, 2, 2),
    "argentina": _record("national", 16, 0, 1, 3, 0, "FIFA and CONMEBOL competition records"),
    "spain": _record("national", 4, 0, 1, 1, 0, "FIFA and UEFA competition records"),
    "france": _record("national", 2, 0, 3, 2, 0, "FIFA and UEFA competition records"),
    "england": _record("national", 0, 0, 0, 1, 0, "FIFA and UEFA competition records"),
    "portugal": _record("national", 1, 0, 1, 0, 0, "UEFA competition records"),
    "brazil": _record("national", 9, 0, 4, 5, 0, "FIFA and CONMEBOL competition records"),
    "netherlands": _record("national", 1, 0, 0, 0, 0, "FIFA and UEFA competition records"),
}


ALIASES = {
    "paris saint germain": "paris saint germain",
    "psg": "paris saint germain",
    "fc internazionale milano": "internazionale",
    "inter milan": "internazionale",
    "inter": "internazionale",
    "ssc napoli": "napoli",
    "as roma": "roma",
    "afc ajax": "ajax",
    "fc barcelona": "barcelona",
    "barcelona": "barcelona",
    "real madrid cf": "real madrid",
    "atletico de madrid": "atletico madrid",
    "atletico madrid": "atletico madrid",
    "bayern munchen": "bayern munich",
    "fc bayern munich": "bayern munich",
    "manchester city fc": "manchester city",
    "manchester united fc": "manchester united",
    "liverpool fc": "liverpool",
    "chelsea fc": "chelsea",
    "arsenal fc": "arsenal",
    "tottenham hotspur fc": "tottenham",
    "aston villa fc": "aston villa",
}


def _key(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9 ]+", " ", name.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return ALIASES.get(normalized, normalized)


def get_club_honours(name: str) -> dict | None:
    """Return a copy so callers cannot mutate the curated catalogue."""
    record = HONOURS.get(_key(name))
    return dict(record) if record else None
