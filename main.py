from dotenv import load_dotenv

load_dotenv()

import argparse
import json
import sys

from research_agent.agent import ResearchAgent
from research_agent.config import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-source web research agent")
    parser.add_argument("question", help="Research question to answer")
    parser.add_argument("--top-n", type=int, default=8, help="Number of ranked sources to use")
    parser.add_argument("--json", action="store_true", help="Print raw JSON output")
    args = parser.parse_args()

    settings = load_settings()
    agent = ResearchAgent(settings)
    result = agent.run(args.question, top_n=args.top_n)

    if args.json:
        print(json.dumps({
            "question": result.question,
            "answer": result.answer,
            "key_claims": result.key_claims,
            "references": [{"title": r.title, "url": r.url} for r in result.references],
            "conflicts": result.conflicts,
            "uncertainties": result.uncertainties,
            "provider_failures": result.provider_failures,
        }, indent=2))
        return

    print(f"\nQuestion: {result.question}\n")
    print(f"Answer:")
    print(f"{result.answer}\n")

    if result.key_claims:
        print("Key claims:")
        for claim in result.key_claims:
            print(f"  - {claim}")
        print()

    if result.references:
        print("References:")
        for i, ref in enumerate(result.references, start=1):
            print(f"  [{i}] {ref.title}")
            print(f"      {ref.url}")
        print()

    if result.conflicts:
        print("Conflicts:")
        for c in result.conflicts:
            print(f"  - {c}")
        print()

    if result.uncertainties:
        print("Uncertainties:")
        for u in result.uncertainties:
            print(f"  - {u}")
        print()

    if result.provider_failures:
        print("Provider failures:")
        for f in result.provider_failures:
            print(f"  - {f}")
        print()


if __name__ == "__main__":
    sys.exit(main())