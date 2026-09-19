from urllib.parse import urlparse, urlunparse

from research_agent.models import ProviderOutcome, SearchResult


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip().lower())
    path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def merge_and_deduplicate(outcomes: list[ProviderOutcome]) -> list[SearchResult]:
    seen: dict[str, SearchResult] = {}
    for outcome in outcomes:
        for result in outcome.results:
            if not result.url:
                continue
            key = normalize_url(result.url)
            existing = seen.get(key)
            if existing is None:
                seen[key] = result
                continue
            # Prefer the version with a longer snippet since it carries more evidence.
            if len(result.snippet) > len(existing.snippet):
                seen[key] = result
    return list(seen.values())
