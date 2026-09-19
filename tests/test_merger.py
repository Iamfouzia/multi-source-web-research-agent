from research_agent.merger import merge_and_deduplicate, normalize_url
from research_agent.models import ProviderOutcome, SearchResult


def test_normalize_url_strips_trailing_slash_and_case():
    assert normalize_url("HTTPS://Example.com/Page/") == "https://example.com/page"


def test_merge_deduplicates_across_providers():
    result_a = SearchResult(title="A", url="https://example.com/page", snippet="short", source_provider="tavily")
    result_b = SearchResult(title="A", url="https://example.com/page/", snippet="much longer snippet text", source_provider="duckduckgo")
    outcomes = [
        ProviderOutcome(provider_name="tavily", results=[result_a]),
        ProviderOutcome(provider_name="duckduckgo", results=[result_b]),
    ]

    merged = merge_and_deduplicate(outcomes)

    assert len(merged) == 1
    assert merged[0].snippet == "much longer snippet text"


def test_merge_keeps_distinct_urls():
    result_a = SearchResult(title="A", url="https://example.com/a", snippet="a", source_provider="tavily")
    result_b = SearchResult(title="B", url="https://example.com/b", snippet="b", source_provider="tavily")
    outcomes = [ProviderOutcome(provider_name="tavily", results=[result_a, result_b])]

    merged = merge_and_deduplicate(outcomes)

    assert len(merged) == 2
