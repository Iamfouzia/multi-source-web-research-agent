from research_agent.models import ProviderOutcome
from research_agent.providers.base import SearchProvider
from research_agent.retry import call_with_retries


def run_providers(
    providers: list[SearchProvider],
    query: str,
    max_results: int,
    timeout: int,
    max_retries: int,
) -> list[ProviderOutcome]:
    outcomes = []
    for provider in providers:
        try:
            results = call_with_retries(
                lambda p=provider: p.search(query, max_results, timeout),
                max_retries=max_retries,
            )
            outcomes.append(ProviderOutcome(provider_name=provider.name, results=results))
        except Exception as exc:
            outcomes.append(
                ProviderOutcome(provider_name=provider.name, succeeded=False, error=str(exc))
            )
    return outcomes
