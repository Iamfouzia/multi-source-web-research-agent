from research_agent.llm_client import GrokClient

_SYSTEM_PROMPT = (
    "You break a research question into 2-4 focused, non-overlapping search queries. "
    "Reply with one query per line, no numbering, no commentary."
)


def plan_queries(client: GrokClient, question: str, max_queries: int = 4) -> list[str]:
    try:
        raw = client.complete(_SYSTEM_PROMPT, question)
        queries = [line.strip("-• \t") for line in raw.splitlines() if line.strip()]
        queries = [q for q in queries if q][:max_queries]
        return queries if queries else [question]
    except Exception:
        return [question]
