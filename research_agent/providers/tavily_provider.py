import requests

from research_agent.models import SearchResult
from research_agent.providers.base import SearchProvider


class TavilyProvider(SearchProvider):
    name = "tavily"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int, timeout: int) -> list[SearchResult]:
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_answer": False,
        }
        response = requests.post(self.endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", "").strip(),
                    url=item.get("url", "").strip(),
                    snippet=item.get("content", "").strip(),
                    source_provider=self.name,
                    published_date=item.get("published_date"),
                )
            )
        return results
