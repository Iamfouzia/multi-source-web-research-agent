from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

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

StageCallback = Callable[[str, Optional[str]], None]


class ResearchAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = GrokClient(settings.grok_api_key, settings.grok_base_url, settings.grok_model)
        self.providers = [
            TavilyProvider(settings.tavily_api_key),
            DuckDuckGoProvider(),
        ]

    def run(
        self,
        question: str,
        top_n: int = 8,
        on_stage: Optional[StageCallback] = None,
    ) -> ResearchAnswer:
        def stage(name: str, detail: Optional[str] = None) -> None:
            if on_stage is not None:
                try:
                    on_stage(name, detail)
                except Exception:
                    pass

        stage("planning")
        queries = plan_queries(self.llm, question)

        stage("searching", f"{len(queries)} sub-quer{'y' if len(queries) == 1 else 'ies'} across {len(self.providers)} providers")
        with ThreadPoolExecutor(max_workers=max(1, len(queries))) as pool:
            futures = [
                pool.submit(
                    run_providers,
                    self.providers,
                    query,
                    self.settings.max_results_per_provider,
                    self.settings.provider_timeout_seconds,
                    self.settings.max_retries,
                )
                for query in queries
            ]
            all_outcomes = []
            for future in futures:
                all_outcomes.extend(future.result())

        provider_failures = [
            f"{o.provider_name}: {o.error}" for o in all_outcomes if not o.succeeded
        ]

        stage("ranking")
        merged = merge_and_deduplicate(all_outcomes)
        ranked_all = rank_results(merged, question)
        top_ranked = filter_top(ranked_all, top_n)

        stage("reading", f"{len(top_ranked)} pages")
        fetch_all([item.result for item in top_ranked], self.settings.fetch_timeout_seconds, self.settings.max_retries)

        top_ranked = rank_results([item.result for item in top_ranked], question)

        stage("synthesizing")
        return synthesize(self.llm, question, top_ranked, provider_failures)