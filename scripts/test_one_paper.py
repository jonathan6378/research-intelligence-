import asyncio
import json

from src.llm.orchestrator import LLMOrchestrator


PAPER_FILE = "data/raw/research_papers_enriched.json"


async def main():

    # -----------------------------------------
    # Load dataset
    # -----------------------------------------

    with open(
        PAPER_FILE,
        encoding="utf-8",
    ) as f:

        papers = json.load(f)


    print("=" * 60)
    print("LOADED PAPERS")
    print("=" * 60)

    print(
        "Total papers:",
        len(papers),
    )


    # -----------------------------------------
    # Select ONE paper
    # -----------------------------------------

    paper = papers[0]


    print("\n" + "=" * 60)
    print("TEST PAPER")
    print("=" * 60)

    print(
        "Title:",
        paper.get("title"),
    )

    print(
        "URL:",
        paper.get("paper_url"),
    )

    print(
        "Authors:",
        len(paper.get("authors", [])),
    )


    # -----------------------------------------
    # Build source text
    # -----------------------------------------

    source_text = json.dumps(
        paper,
        ensure_ascii=False,
        indent=2,
    )


    print("\nSource characters:")

    print(
        len(source_text)
    )


    # -----------------------------------------
    # Initialize engine
    # -----------------------------------------

    engine = LLMOrchestrator()


    print("\n" + "=" * 60)
    print("CALLING LLM")
    print("=" * 60)


    result = await engine.extract(
        record_type="RESEARCH_PAPER",
        text=source_text,
    )


    # -----------------------------------------
    # Display result
    # -----------------------------------------

    print("\n" + "=" * 60)
    print("LLM RESULT")
    print("=" * 60)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":

    asyncio.run(main())