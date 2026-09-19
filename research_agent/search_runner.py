from concurrent.futures import ThreadPoolExecutor

from research_agent.models import ProviderOutcome
from research_agent.providers.base import SearchProvider
from research_agent.retry import call_with_retries


def _run_one(
    provider: SearchProvider,
    query: str,
    max_results: int,
    timeout: int,
    max_retries: int,
) -> ProviderOutcome:
    try:
        results = call_with_retries(
            lambda: provider.search(query, max_results, timeout),
            max_retries=max_retries,
        )
        return ProviderOutcome(provider_name=provider.name, results=results)
    except Exception as exc:
        return ProviderOutcome(provider_name=provider.name, succeeded=False, error=str(exc))


def run_providers(
    providers: list[SearchProvider],
    query: str,
    max_results: int,
    timeout: int,
    max_retries: int,
) -> list[ProviderOutcome]:
    if not providers:
        return []
    with ThreadPoolExecutor(max_workers=len(providers)) as pool:
        futures = [
            pool.submit(_run_one, provider, query, max_results, timeout, max_retries)
            for provider in providers
        ]
        return [future.result() for future in futures]