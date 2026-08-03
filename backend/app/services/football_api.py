import time

import requests
from requests.exceptions import ConnectionError, Timeout

from app.core.config import settings


class FootballAPIClient:
    """
    Client responsible for communicating with
    the Football-Data.org API.
    """

    def __init__(self):
        self.base_url = settings.FOOTBALL_API_BASE_URL
        self.api_key = settings.FOOTBALL_API_KEY

        self.headers = {
            "X-Auth-Token": self.api_key
        }

        self.timeout = settings.REQUEST_TIMEOUT

        # Delay between requests
        self.request_delay = 0.5

        # Maximum retry attempts
        self.max_retries = 5

    def get(self, endpoint: str, params: dict | None = None):
        """
        Sends a GET request to the Football-Data.org API.

        Handles:

        ✓ 200 -> Success
        ✓ 429 -> Wait and Retry
        ✓ 500/502/503/504 -> Retry
        ✓ Timeout -> Retry
        ✓ ConnectionError -> Retry

        ✗ 400 -> Skip
        ✗ 401 -> Skip
        ✗ 403 -> Skip
        ✗ 404 -> Skip
        ✗ Any other 4xx -> Skip
        """

        url = f"{self.base_url}{endpoint}"

        retries = 0

        while retries <= self.max_retries:

            try:

                time.sleep(self.request_delay)

                response = requests.get(
                    url=url,
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout
                )

                status = response.status_code

                # --------------------------------------------------
                # SUCCESS
                # --------------------------------------------------

                if status == 200:
                    return response.json()

                # --------------------------------------------------
                # RATE LIMIT
                # --------------------------------------------------

                if status == 429:

                    retry_after = response.headers.get("Retry-After")

                    try:
                        wait_time = int(retry_after)
                    except (TypeError, ValueError):
                        wait_time = 60

                    retries += 1

                    print(
                        f"\n[429] Rate limit reached."
                        f"\nWaiting {wait_time} seconds..."
                        f"\nRetry {retries}/{self.max_retries}\n"
                    )

                    time.sleep(wait_time)

                    continue

                # --------------------------------------------------
                # SERVER ERRORS
                # --------------------------------------------------

                if status in (500, 502, 503, 504):

                    retries += 1

                    wait_time = retries * 5

                    print(
                        f"\n[{status}] Server error."
                        f"\nRetry {retries}/{self.max_retries}"
                        f" in {wait_time} seconds.\n"
                    )

                    time.sleep(wait_time)

                    continue

                # --------------------------------------------------
                # CLIENT ERRORS (DO NOT RETRY)
                # --------------------------------------------------

                if 400 <= status < 500:

                    print(
                        f"\n[{status}] Skipping endpoint: {endpoint}\n"
                    )

                    return None

                # --------------------------------------------------
                # UNKNOWN STATUS
                # --------------------------------------------------

                print(
                    f"\nUnexpected HTTP status {status}"
                    f" for endpoint: {endpoint}\n"
                )

                return None

            except Timeout:

                retries += 1

                wait_time = retries * 5

                print(
                    f"\nTimeout."
                    f"\nRetry {retries}/{self.max_retries}"
                    f" in {wait_time} seconds.\n"
                )

                time.sleep(wait_time)

            except ConnectionError:

                retries += 1

                wait_time = retries * 5

                print(
                    f"\nConnection error."
                    f"\nRetry {retries}/{self.max_retries}"
                    f" in {wait_time} seconds.\n"
                )

                time.sleep(wait_time)

        raise Exception(
            f"Maximum retries exceeded while requesting {endpoint}"
        )