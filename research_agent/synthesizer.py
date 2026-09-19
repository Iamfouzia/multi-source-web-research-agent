import json

from research_agent.llm_client import GrokClient
from research_agent.models import RankedResult, ResearchAnswer

_SYSTEM_PROMPT = """You are a research assistant that answers strictly from provided evidence.
Each evidence item has an index, title, url, a short summary, and a longer page excerpt.
The page excerpt may occasionally be low-quality (navigation text, cookie banners) if the
page could not be fully read; in that case rely on the summary instead. Use only these
items as sources. If evidence is missing or conflicting, state that explicitly instead of
guessing.

Write the answer as clear, professional prose in 2-4 well-formed sentences, as if for a
briefing document. Cite at most 1-2 sources per sentence using [n] notation immediately
after the relevant clause, not stacked at the end of a sentence. Do not pile more than
two citation numbers together (e.g. avoid "[1][2][7][8]"). Prefer the single most
relevant source per claim.

Respond with valid JSON only, in this exact shape:
{
  "answer": "concise, professionally written answer with sparing inline [n] citations",
  "key_claims": ["one clear, well-written sentence per claim, each ending with a single [n] citation", "..."],
  "conflicts": ["description of any contradiction between sources, or empty list"],
  "uncertainties": ["material gaps or unanswered aspects, or empty list"]
}
No text outside the JSON object."""


def _build_evidence_block(ranked: list[RankedResult]) -> str:
    lines = []
    for i, item in enumerate(ranked, start=1):
        snippet = item.result.snippet[:500]
        content = (item.result.content or "")[:800]
        lines.append(
            f"[{i}] {item.result.title}\nURL: {item.result.url}\n"
            f"Summary: {snippet}\nPage excerpt: {content}"
        )
    return "\n\n".join(lines)


def _parse_json_response(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
    return json.loads(cleaned)


def synthesize(
    client: GrokClient,
    question: str,
    ranked: list[RankedResult],
    provider_failures: list[str],
) -> ResearchAnswer:
    if not ranked:
        return ResearchAnswer(
            question=question,
            answer="No usable evidence was retrieved for this question.",
            key_claims=[],
            references=[],
            conflicts=[],
            uncertainties=["All providers returned zero usable results."],
            provider_failures=provider_failures,
        )

    evidence_block = _build_evidence_block(ranked)
    user_prompt = f"Research question: {question}\n\nEvidence:\n{evidence_block}"

    try:
        raw_response = client.complete(_SYSTEM_PROMPT, user_prompt, timeout=45)
        parsed = _parse_json_response(raw_response)
    except Exception as exc:
        return ResearchAnswer(
            question=question,
            answer="Synthesis failed due to an LLM or parsing error; raw evidence is listed in references.",
            key_claims=[],
            references=[item.result for item in ranked],
            conflicts=[],
            uncertainties=[f"Synthesis error: {exc}"],
            provider_failures=provider_failures,
        )

    return ResearchAnswer(
        question=question,
        answer=parsed.get("answer", ""),
        key_claims=parsed.get("key_claims", []),
        references=[item.result for item in ranked],
        conflicts=parsed.get("conflicts", []),
        uncertainties=parsed.get("uncertainties", []),
        provider_failures=provider_failures,
    )