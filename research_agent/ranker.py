import re

from research_agent.models import RankedResult, SearchResult

_WORD_RE = re.compile(r"[a-z0-9]+")

_LOW_QUALITY_DOMAINS = {"pinterest.com", "quora.com"}


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _domain(url: str) -> str:
    match = re.search(r"://([^/]+)/?", url + "/")
    return match.group(1).lower() if match else ""


def score_result(result: SearchResult, query_tokens: set[str]) -> RankedResult:
    text_tokens = _tokenize(result.title + " " + result.snippet + " " + (result.content or ""))
    overlap = len(query_tokens & text_tokens)
    overlap_score = overlap / max(len(query_tokens), 1)

    has_content_bonus = 0.15 if result.content else 0.0

    domain = _domain(result.url)
    quality_penalty = 0.3 if any(bad in domain for bad in _LOW_QUALITY_DOMAINS) else 0.0

    final_score = round(min(1.0, overlap_score + has_content_bonus - quality_penalty), 3)
    reason = f"lexical overlap={overlap}, has_full_content={bool(result.content)}, domain={domain}"
    return RankedResult(result=result, score=final_score, reason=reason)


def rank_results(results: list[SearchResult], query: str) -> list[RankedResult]:
    query_tokens = _tokenize(query)
    ranked = [score_result(result, query_tokens) for result in results]
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked


def filter_top(ranked: list[RankedResult], top_n: int, min_score: float = 0.05) -> list[RankedResult]:
    filtered = [r for r in ranked if r.score >= min_score]
    return filtered[:top_n] if filtered else ranked[:top_n]
