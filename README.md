# Multi-Source Web Research Agent

A research agent that answers a natural-language question by querying two independent
search providers, merging and ranking the results, fetching full page content, and
synthesizing a grounded answer with citations using an LLM (Grok).

## Problem Understanding

A single search-result-to-LLM chain is fragile: one provider's blind spots become the
system's blind spots, duplicate or near-duplicate results waste context, and an LLM
asked to "just answer" will happily fill gaps with unsupported claims. This project
treats retrieval and synthesis as separate, testable stages, and requires the final
answer to be traceable back to specific fetched sources rather than model memory.

## Architecture

```
question
   │
   ▼
planner.py          -> decomposes the question into 2-4 focused sub-queries (LLM)
   │
   ▼
search_runner.py     -> runs each sub-query against every provider, isolates failures
   │                    providers/tavily_provider.py, providers/duckduckgo_provider.py
   ▼
merger.py            -> normalizes URLs, deduplicates across providers and sub-queries
   │
   ▼
ranker.py             -> scores results by lexical overlap + content/domain signals
   │
   ▼
fetcher.py             -> fetches full page text for the top-ranked candidates
   │
   ▼
ranker.py (re-rank)    -> re-scores using full content, not just snippets
   │
   ▼
synthesizer.py         -> LLM produces answer + key claims + conflicts + uncertainties,
   │                       grounded only in the fetched evidence (JSON-constrained)
   ▼
main.py                -> CLI entrypoint, formats final output
```

Each stage is a separate module with a narrow interface (`list[SearchResult] in, list[SearchResult] out`,
or equivalent), so any stage can be tested, replaced, or extended independently.

## Technology Choices

- **Search providers**: Tavily (LLM-oriented search API, good snippet quality) and
  DuckDuckGo (via the `ddgs` library, free, no API key). Two providers with different
  indexing and ranking behavior reduces the chance both miss the same evidence.
- **LLM**: Grok (`grok-4-fast` via xAI's OpenAI-compatible `/chat/completions` endpoint),
  chosen for its free tier and simple integration via `requests`.
- **HTTP**: plain `requests` with a shared retry/backoff helper — no heavier framework
  needed for this scope.
- **No agent framework** (e.g. LangChain): the pipeline is a fixed, well-understood
  sequence of stages, so an explicit orchestrator (`agent.py`) is more debuggable and
  has no hidden prompt/tool-call behavior to reason about.

## Key Engineering Decisions

- **Deduplication**: URLs are normalized (scheme+host+path, lowercased, trailing slash
  stripped, query/fragment dropped) before comparison. When two providers return the
  same URL, the result with the longer snippet is kept, since it carries more usable
  evidence for ranking.
- **Ranking**: relevance is scored by lexical token overlap between the query and the
  result's title/snippet/content, with a bonus for having successfully fetched full
  content and a penalty for known low-signal domains. This is intentionally simple and
  explainable rather than a black-box embedding score — the ranking reason is stored
  alongside each score.
- **Conflict/uncertainty handling**: the synthesizer's system prompt explicitly
  instructs the LLM to report contradictions between sources and any question aspects
  the evidence doesn't cover, returned as separate `conflicts` and `uncertainties`
  fields rather than folded into prose.
- **Hallucination reduction**: the synthesis prompt restricts the LLM to the numbered
  evidence block only, requires inline `[n]` citations, and forces valid-JSON output so
  answers can be programmatically checked against the reference list.
- **Failure handling**: each provider call is wrapped individually — one provider
  failing (timeout, rate limit, bad response) does not stop the pipeline; its error is
  recorded and surfaced in the final output as `provider_failures`. `call_with_retries`
  applies exponential backoff to both provider calls and page fetches. If synthesis
  itself fails (LLM error or malformed JSON), the agent falls back to returning the raw
  ranked evidence rather than crashing.
- **Credentials**: all keys are read from environment variables via `config.py`; `.env`
  is git-ignored, and `.env.example` documents required variables without real values.

## Known Limitations

- Ranking is lexical, not semantic — synonyms or paraphrased evidence may score lower
  than a true embedding-based approach would.
- Page fetching does a basic HTML-tag strip, not full readability extraction, so
  JS-rendered pages or heavy boilerplate can reduce content quality.
- DuckDuckGo's unofficial search endpoint (via `ddgs`) can be rate-limited more
  aggressively than a paid API; retries mitigate but don't eliminate this.
- No caching layer — repeated identical questions re-run the full pipeline.
- No automated evaluation harness for answer quality (only unit tests for the
  deterministic modules: merging, ranking, retry logic).

## Possible Future Improvements

- Swap lexical ranking for embedding-based similarity, with the current heuristic as a
  fallback when embeddings are unavailable.
- Add a lightweight cache keyed on normalized query + provider.
- Add a verification pass that re-checks each key claim against its cited source before
  returning the answer.
- Add a third, structurally different provider (e.g. a news or academic API) to
  broaden source diversity further.

## Setup

**Requirements**: Python 3.10+

```bash
git clone <repository-url>
cd research-agent
pip install -r requirements.txt
cp .env.example .env
# edit .env and fill in GROK_API_KEY and TAVILY_API_KEY
```

- Get a free Grok API key: https://console.x.ai
- Get a free Tavily API key: https://tavily.com

## Execution

```bash
python main.py "What are the main risks of quantum computing to current encryption?"
```

Optional flags:

```bash
python main.py "your question" --top-n 10       # use more ranked sources
python main.py "your question" --json            # machine-readable output
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Tests cover the deterministic core: URL normalization/deduplication, lexical ranking
and filtering, and retry-with-backoff behavior. LLM and network-dependent modules
(providers, synthesizer) are excluded from unit tests since they require live API keys;
they are instead exercised end-to-end via the CLI, as shown in the demo video.

## Implementation Note

All modules in this repository (`config`, `models`, `retry`, `providers/*`, `search_runner`,
`merger`, `fetcher`, `ranker`, `planner`, `synthesizer`, `llm_client`, `agent`, `main`, and
the test suite) were personally implemented for this assignment. Design decisions,
trade-offs, and known failure cases are documented above; the same points are walked
through in the demo video alongside a live run.
