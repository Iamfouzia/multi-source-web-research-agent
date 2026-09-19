import re
from concurrent.futures import ThreadPoolExecutor

import requests

from research_agent.models import SearchResult
from research_agent.retry import call_with_retries

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def _strip_html(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    return _WHITESPACE_RE.sub(" ", text).strip()


def fetch_content(result: SearchResult, timeout: int, max_retries: int, char_limit: int = 4000) -> None:
    try:
        response = call_with_retries(
            lambda: requests.get(
                result.url,
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (research-agent)"},
            ),
            max_retries=max_retries,
            retry_on=(requests.RequestException,),
        )
        response.raise_for_status()
        result.content = _strip_html(response.text)[:char_limit]
    except Exception:
        result.content = None


def fetch_all(results: list[SearchResult], timeout: int, max_retries: int, max_workers: int = 8) -> None:
    if not results:
        return
    with ThreadPoolExecutor(max_workers=min(max_workers, len(results))) as pool:
        list(pool.map(lambda result: fetch_content(result, timeout, max_retries), results))