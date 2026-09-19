from ddgs import DDGS

from research_agent.models import SearchResult
from research_agent.providers.base import SearchProvider


class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"

    def search(self, query: str, max_results: int, timeout: int) -> list[SearchResult]:
        results = []
        with DDGS(timeout=timeout) as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                results.append(
                    SearchResult(
                        title=item.get("title", "").strip(),
                        url=item.get("href", "").strip(),
                        snippet=item.get("body", "").strip(),
                        source_provider=self.name,
                    )
                )
        return results
