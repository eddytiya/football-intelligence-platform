import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from etl.config.settings import settings
from etl.utils.logger import logger


class APIClient:
    def __init__(self, base_url: str, headers: dict | None = None):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=settings.REQUEST_TIMEOUT,
            headers=self.headers,
        )

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_fixed(settings.RETRY_DELAY),
        reraise=True,
    )
    def get(self, endpoint: str, params: dict | None = None):
        logger.info(
            f"GET {endpoint} | params={params}"
        )

        response = self.client.get(endpoint, params=params)

        response.raise_for_status()

        return response.json()

    def close(self):
        self.client.close()