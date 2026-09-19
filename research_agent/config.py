import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    grok_api_key: str
    grok_base_url: str
    grok_model: str
    tavily_api_key: str
    max_results_per_provider: int
    fetch_timeout_seconds: int
    provider_timeout_seconds: int
    max_retries: int


def load_settings() -> Settings:
    grok_api_key = os.environ.get("GROK_API_KEY", "")
    if not grok_api_key:
        raise RuntimeError("GROK_API_KEY is not set in the environment")

    tavily_api_key = os.environ.get("TAVILY_API_KEY", "")
    if not tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY is not set in the environment")

    return Settings(
        grok_api_key=grok_api_key,
        grok_base_url=os.environ.get("GROK_BASE_URL", "https://api.x.ai/v1"),
        grok_model=os.environ.get("GROK_MODEL", "grok-4-fast"),
        tavily_api_key=tavily_api_key,
        max_results_per_provider=int(os.environ.get("MAX_RESULTS_PER_PROVIDER", "5")),
        fetch_timeout_seconds=int(os.environ.get("FETCH_TIMEOUT_SECONDS", "10")),
        provider_timeout_seconds=int(os.environ.get("PROVIDER_TIMEOUT_SECONDS", "12")),
        max_retries=int(os.environ.get("MAX_RETRIES", "2")),
    )
