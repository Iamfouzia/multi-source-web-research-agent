from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source_provider: str
    published_date: Optional[str] = None
    content: Optional[str] = None
    relevance_score: float = 0.0


@dataclass
class ProviderOutcome:
    provider_name: str
    results: list[SearchResult] = field(default_factory=list)
    error: Optional[str] = None
    succeeded: bool = True


@dataclass
class RankedResult:
    result: SearchResult
    score: float
    reason: str


@dataclass
class ResearchAnswer:
    question: str
    answer: str
    key_claims: list[str]
    references: list[SearchResult]
    conflicts: list[str]
    uncertainties: list[str]
    provider_failures: list[str]
