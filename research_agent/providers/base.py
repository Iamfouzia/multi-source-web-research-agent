from abc import ABC, abstractmethod

from research_agent.models import SearchResult


class SearchProvider(ABC):
    name: str

    @abstractmethod
    def search(self, query: str, max_results: int, timeout: int) -> list[SearchResult]:
        raise NotImplementedError
