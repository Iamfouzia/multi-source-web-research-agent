# 🔎 Multi-Source Web Research Agent

A research agent that answers a natural-language question by querying **two independent
search providers**, merging and deduplicating the results, fetching full page content,
ranking sources by relevance, and synthesizing a **grounded, citation-backed answer**
using an LLM — instead of relying on a single search-result-to-answer chain.

Built as part of the **Zephra AI — AI/ML Internship Technical Assessment (Track A)**.

---

## 🚀 Features

* 🧠 LLM-based question planning/decomposition into focused sub-queries
* 🔗 Multi-source retrieval — Tavily + DuckDuckGo (two independent providers)
* 🧹 URL normalization, merging, and deduplication across sources
* 📄 Full-page content fetching for top-ranked candidates
* 📊 Explainable relevance ranking (lexical overlap + content/domain signals)
* 📝 Evidence-grounded synthesis with inline `[n]` citations
* ⚠️ Explicit conflict and uncertainty reporting — no silent guessing
* 🔁 Retry-with-backoff and isolated failure handling per provider
* 🧪 Unit-tested core (merging, ranking, retry logic)
* 🔐 Environment-variable based credentials — nothing hardcoded or committed

---

## 🏗️ Project Structure

```text
research-agent/
│
├── main.py                  # CLI entrypoint
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .gitignore
│
├── research_agent/
│   ├── agent.py              # Orchestrator wiring the full pipeline
│   ├── config.py             # Environment-based settings loader
│   ├── models.py             # Shared data models
│   ├── planner.py            # Question decomposition (LLM)
│   ├── search_runner.py      # Runs providers with retries, isolates failures
│   ├── merger.py             # URL normalization, merge, deduplication
│   ├── ranker.py             # Lexical relevance scoring and filtering
│   ├── fetcher.py            # Full page content retrieval
│   ├── synthesizer.py        # Evidence-grounded answer generation
│   ├── llm_client.py         # LLM API client
│   ├── retry.py              # Shared retry/backoff helper
│   └── providers/
│       ├── base.py
│       ├── tavily_provider.py
│       └── duckduckgo_provider.py
│
└── tests/
    ├── test_merger.py
    ├── test_ranker.py
    └── test_retry.py
```

---

## 🧩 Architecture

```text
question
   │
   ▼
planner.py            → decomposes the question into 2-4 focused sub-queries (LLM)
   │
   ▼
search_runner.py       → runs each sub-query against every provider, isolates failures
   │                      providers/tavily_provider.py, providers/duckduckgo_provider.py
   ▼
merger.py               → normalizes URLs, deduplicates across providers and sub-queries
   │
   ▼
ranker.py                → scores results by lexical overlap + content/domain signals
   │
   ▼
fetcher.py                 → fetches full page text for the top-ranked candidates
   │
   ▼
ranker.py (re-rank)         → re-scores using full content, not just snippets
   │
   ▼
synthesizer.py                → produces answer + key claims + conflicts + uncertainties,
   │                              grounded only in fetched evidence (JSON-constrained)
   ▼
main.py                          → CLI entrypoint, formats final output
```

Each stage is a separate module with a narrow, testable interface, so any stage can be
replaced or extended independently — for example, swapping the ranking heuristic for an
embedding-based approach without touching retrieval or synthesis.

---

## 🛠️ Technology Stack

| Category          | Choice                                      |
| ------------------ | -------------------------------------------- |
| Language           | Python 3.10+                                 |
| Search providers   | Tavily API, DuckDuckGo (`ddgs`)              |
| LLM                | Groq API (OpenAI-compatible `/chat/completions`) |
| HTTP client        | `requests` with shared retry/backoff logic    |
| Testing            | Pytest                                        |
| Config             | Environment variables via `python-dotenv`     |

**Why these choices:**

- **Tavily + DuckDuckGo** — two providers with different indexing and ranking behavior,
  reducing the chance both miss the same evidence. Tavily is tuned for LLM-oriented
  search quality; DuckDuckGo adds a free, independent second signal.
- **Groq** — fast, free-tier LLM inference via an OpenAI-compatible API, used purely for
  planning and synthesis, never as the source of factual claims.
- **No agent framework** (e.g. LangChain) — the pipeline is a fixed, well-understood
  sequence of stages, so an explicit orchestrator (`agent.py`) is easier to debug and has
  no hidden prompt/tool-call behavior to reason about.

---

## 📋 Prerequisites

* Python 3.10+
* pip
* A free [Groq API key](https://console.groq.com/keys)
* A free [Tavily API key](https://tavily.com)

---

## 📥 Installation

**1. Clone the repository**

```bash
git clone https://github.com/Iamfouzia/multi-source-web-research-agent.git
cd multi-source-web-research-agent
```

**2. (Optional) Create a virtual environment**

```bash
python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```env
GROK_API_KEY=your_groq_api_key
GROK_BASE_URL=https://api.groq.com/openai/v1
GROK_MODEL=openai/gpt-oss-20b

TAVILY_API_KEY=your_tavily_api_key

MAX_RESULTS_PER_PROVIDER=5
FETCH_TIMEOUT_SECONDS=10
PROVIDER_TIMEOUT_SECONDS=12
MAX_RETRIES=2
```

> **Never commit real API keys.** `.env` is already listed in `.gitignore`.

---

## ▶️ Running the Agent

```bash
python main.py "What are the main risks of quantum computing to current encryption?"
```

Optional flags:

```bash
python main.py "your question" --top-n 10   # use more ranked sources
python main.py "your question" --json       # machine-readable output
```

**Example output includes:**
- A concise, evidence-grounded answer with inline `[n]` citations
- Key claims, each traceable to a specific source
- A numbered reference list with titles and URLs
- Any detected conflicts between sources
- Explicitly flagged uncertainties or missing evidence

---

## 🧪 Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Tests cover the deterministic core: URL normalization/deduplication, lexical ranking and
filtering, and retry-with-backoff behavior. LLM and network-dependent modules (providers,
synthesizer) are exercised end-to-end via the CLI rather than unit tests, since they
require live API keys — this is demonstrated in the demo video.

---

## 🧠 Key Engineering Decisions

- **Deduplication** — URLs are normalized (scheme + host + path, lowercased, trailing
  slash stripped, query/fragment dropped) before comparison. When two providers return
  the same URL, the result with the longer snippet is kept, since it carries more usable
  evidence for ranking.
- **Ranking** — relevance is scored by lexical token overlap between the query and the
  result's title/snippet/content, with a bonus for successfully fetched full content and
  a penalty for known low-signal domains. This is intentionally simple and explainable
  rather than a black-box embedding score — the ranking reason is stored alongside each
  score.
- **Conflict/uncertainty handling** — the synthesizer's prompt explicitly instructs the
  LLM to report contradictions between sources and any question aspects the evidence
  doesn't cover, returned as separate `conflicts` and `uncertainties` fields rather than
  folded into prose.
- **Hallucination reduction** — the synthesis prompt restricts the LLM to the numbered
  evidence block only, requires inline `[n]` citations, and forces valid-JSON output so
  answers can be programmatically checked against the reference list. When a fetched
  page yields low-quality content (navigation text, cookie banners), the LLM is
  instructed to fall back to the provider's search snippet instead.
- **Failure handling** — each provider call is wrapped individually; one provider
  failing (timeout, rate limit, bad response) does not stop the pipeline — its error is
  recorded and surfaced in the final output as `provider_failures`. `call_with_retries`
  applies exponential backoff to both provider calls and page fetches. If synthesis
  itself fails, the agent falls back to returning the raw ranked evidence rather than
  crashing.
- **Credentials** — all keys are read from environment variables via `config.py`; `.env`
  is git-ignored, and `.env.example` documents required variables without real values.

---

## ⚠️ Known Limitations

- Ranking is lexical, not semantic — synonyms or paraphrased evidence may score lower
  than a true embedding-based approach would.
- Page fetching does a basic HTML-tag strip, not full readability extraction, so
  JS-rendered pages or heavy boilerplate can reduce content quality (mitigated by
  falling back to the search snippet during synthesis).
- DuckDuckGo's unofficial search endpoint (via `ddgs`) can be rate-limited more
  aggressively than a paid API; retries mitigate but don't eliminate this.
- No caching layer — repeated identical questions re-run the full pipeline.
- No automated evaluation harness for answer quality (only unit tests for the
  deterministic modules: merging, ranking, retry logic).

---

## 🔭 Possible Future Improvements

- Swap lexical ranking for embedding-based similarity, with the current heuristic as a
  fallback when embeddings are unavailable.
- Add a lightweight cache keyed on normalized query + provider.
- Add a verification pass that re-checks each key claim against its cited source before
  returning the answer.
- Add a third, structurally different provider (e.g. a news or academic API) to broaden
  source diversity further.

---

## 👩‍💻 Implementation Note

All modules in this repository (`config`, `models`, `retry`, `providers/*`,
`search_runner`, `merger`, `fetcher`, `ranker`, `planner`, `synthesizer`, `llm_client`,
`agent`, `main`, and the test suite) were personally implemented for this assessment.
Design decisions, trade-offs, and known failure cases are documented above and are
walked through in the accompanying demo video alongside a live run.

---

## 📄 Submission

**Project:** Multi-Source Web Research Agent — Zephra AI AI/ML Internship Assessment (Track A)

**GitHub Repository:** https://github.com/Iamfouzia/multi-source-web-research-agent
