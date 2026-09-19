from research_agent.models import SearchResult
from research_agent.ranker import filter_top, rank_results


def test_rank_results_orders_by_relevance():
    relevant = SearchResult(
        title="Rust memory safety",
        url="https://a.com",
        snippet="Rust prevents memory safety bugs using ownership",
        source_provider="tavily",
    )
    irrelevant = SearchResult(
        title="Weather forecast",
        url="https://b.com",
        snippet="Sunny with a chance of rain",
        source_provider="tavily",
    )

    ranked = rank_results([irrelevant, relevant], "rust memory safety")

    assert ranked[0].result.url == "https://a.com"


def test_filter_top_respects_limit():
    results = [
        SearchResult(title=f"T{i}", url=f"https://x.com/{i}", snippet="python programming", source_provider="tavily")
        for i in range(5)
    ]
    ranked = rank_results(results, "python programming")

    top = filter_top(ranked, top_n=2)

    assert len(top) == 2
