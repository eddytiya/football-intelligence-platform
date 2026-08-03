import logging

from fastapi import APIRouter, Query

from app.core.config import settings
from app.services.news.news_client import get_headlines


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["News"])


@router.get("")
def get_news(
    query: str | None = Query(default=None, max_length=100),
    page_size: int = Query(default=12, ge=1, le=30),
):
    """
    Return recent football headlines for any search term (a club name, a
    competition, or general football news). Works out of the box via a free
    keyless source; automatically upgrades to NewsAPI if NEWS_API_KEY is set.
    """

    try:
        articles = get_headlines(query, page_size)
    except Exception:
        logger.exception("Failed to fetch news headlines")
        return {"articles": [], "error": "The news feed is temporarily unavailable."}

    return {"articles": articles, "provider": "newsapi" if settings.NEWS_API_KEY else "bing_news_rss"}
