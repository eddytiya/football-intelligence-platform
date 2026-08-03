"""Small client for API-Football's squad endpoints."""

import time

import requests

from app.core.config import settings


class APIFootballClient:
    def __init__(self):
        self.base_url = settings.API_FOOTBALL_BASE_URL.rstrip("/")
        self.api_key = settings.API_FOOTBALL_KEY

    def get(self, endpoint: str, params: dict | None = None) -> dict | None:
        if not self.api_key:
            return None
        response = requests.get(
            f"{self.base_url}{endpoint}", params=params, timeout=settings.REQUEST_TIMEOUT,
            headers={"x-apisports-key": self.api_key},
        )
        if response.status_code != 200:
            return None
        return response.json()

    @staticmethod
    def pause_for_free_tier():
        # API-Football's free plan allows 10 requests per minute.
        time.sleep(6.2)
