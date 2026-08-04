import re
import time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlparse

import requests

from app.core.config import settings

# Kept short: news staleness matters more than shielding a free provider
# from load, and Bing's RSS feed only ever returns ~10-12 items anyway.
CACHE_TTL_SECONDS = 180
BING_NEWS_RSS_URL = "https://www.bing.com/news/search"

_cache: dict[tuple[str, int], tuple[float, list[dict]]] = {}


def _map_newsapi_article(article: dict) -> dict:
    return {
        "title": article.get("title"),
        "description": article.get("description"),
        "url": article.get("url"),
        "image": article.get("urlToImage"),
        "source": (article.get("source") or {}).get("name"),
        "published_at": article.get("publishedAt"),
    }


def _fetch_from_newsapi(query: str | None, page_size: int) -> list[dict]:
    response = requests.get(
        f"{settings.NEWS_API_BASE_URL}/everything",
        params={
            "apiKey": settings.NEWS_API_KEY,
            "q": f"{query} football" if query else "soccer",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
        },
        timeout=10,
    )
    response.raise_for_status()
    return [_map_newsapi_article(article) for article in response.json().get("articles", [])]


def _strip_html(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ").strip()
    return cleaned or None


def _local_tag(element) -> str:
    tag = element.tag
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _resolve_bing_link(link: str | None) -> str | None:
    """Bing wraps the real article URL in a tracking link; unwrap it."""

    if not link:
        return link
    destination = parse_qs(urlparse(link).query).get("url")
    return destination[0] if destination else link


def _resolve_bing_image(fields: dict) -> str | None:
    """Bing serves a small default thumbnail; request its largest available size."""

    image_url = fields.get("Image")
    size_template = fields.get("ImageSize")
    max_width = fields.get("ImageMaxWidth")
    max_height = fields.get("ImageMaxHeight")
    if not image_url:
        return None
    if size_template and max_width and max_height:
        return f"{image_url}&{size_template.format(max_width, max_height)}"
    return image_url


def _fetch_from_bing_news_rss(query: str | None, page_size: int) -> list[dict]:
    """
    A free, keyless headline source with real thumbnails and direct article
    links included right in the feed, so no scraping is needed.
    """

    search_term = f"{query} football" if query else "world football"
    response = requests.get(
        BING_NEWS_RSS_URL,
        params={"q": search_term, "format": "RSS"},
        headers={"User-Agent": "Mozilla/5.0 (compatible; FootballIntelligenceBot/1.0)"},
        timeout=10,
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    articles = []
    for item in root.findall(".//item"):
        fields = {_local_tag(child): child.text for child in item}
        articles.append({
            "title": fields.get("title"),
            "description": _strip_html(fields.get("description")),
            "url": _resolve_bing_link(fields.get("link")),
            "image": _resolve_bing_image(fields),
            "source": fields.get("Source"),
            "published_at": fields.get("pubDate"),
        })

    # Bing ranks by relevance, not recency, so the newest article often
    # isn't first. Re-sort by actual publish time so "latest" means latest.
    dated, undated = [], []
    for article in articles:
        try:
            dated.append((parsedate_to_datetime(article["published_at"]), article))
        except (TypeError, ValueError):
            undated.append(article)
    dated.sort(key=lambda pair: pair[0], reverse=True)
    return [article for _, article in dated][:page_size] + undated[:max(0, page_size - len(dated))]


def get_headlines(query: str | None, page_size: int = 12) -> list[dict]:
    """
    Fetch recent football headlines. Uses NewsAPI when a key is configured
    (an alternative structured provider); otherwise falls back to the free,
    keyless Bing News RSS search so the feature works with zero setup.

    Cached per (query, page_size) to be a considerate client of either source.
    """

    cache_key = (query or "world football", page_size)
    cached = _cache.get(cache_key)
    if cached and (time.time() - cached[0]) < CACHE_TTL_SECONDS:
        return cached[1]

    if settings.NEWS_API_KEY:
        articles = _fetch_from_newsapi(query, page_size)
    else:
        articles = _fetch_from_bing_news_rss(query, page_size)

    _cache[cache_key] = (time.time(), articles)
    return articles
