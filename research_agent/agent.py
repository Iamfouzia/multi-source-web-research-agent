from research_agent.config import Settings
from research_agent.fetcher import fetch_all
from research_agent.llm_client import GrokClient
from research_agent.merger import merge_and_deduplicate
from research_agent.models import ResearchAnswer
from research_agent.planner import plan_queries
from research_agent.providers.duckduckgo_provider import DuckDuckGoProvider
from research_agent.providers.tavily_provider import TavilyProvider
from research_agent.ranker import filter_top, rank_results
from research_agent.search_runner import run_providers
from research_agent.synthesizer import synthesize


class ResearchAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = GrokClient(settings.grok_api_key, settings.grok_base_url, settings.grok_model)
        self.providers = [
            TavilyProvider(settings.tavily_api_key),
            DuckDuckGoProvider(),
        ]

    def run(self, question: str, top_n: int = 8) -> ResearchAnswer:
        queries = plan_queries(self.llm, question)

        all_outcomes = []
        for query in queries:
            all_outcomes.extend(
                run_providers(
                    self.providers,
                    query,
                    self.settings.max_results_per_provider,
                    self.settings.provider_timeout_seconds,
                    self.settings.max_retries,
                )
            )

        provider_failures = [
            f"{o.provider_name}: {o.error}" for o in all_outcomes if not o.succeeded
        ]

        merged = merge_and_deduplicate(all_outcomes)
        ranked_all = rank_results(merged, question)
        top_ranked = filter_top(ranked_all, top_n)

        fetch_all([item.result for item in top_ranked], self.settings.fetch_timeout_seconds, self.settings.max_retries)

        # Re-rank after fetching since full content changes lexical overlap signal.
        top_ranked = rank_results([item.result for item in top_ranked], question)

        return synthesize(self.llm, question, top_ranked, provider_failures)
