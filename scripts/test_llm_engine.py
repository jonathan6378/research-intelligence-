import asyncio
from src.llm.orchestrator import LLMOrchestrator


async def main():
    print("=" * 60)
    print("TESTING LLM ORCHESTRATOR")
    print("=" * 60)

    engine = LLMOrchestrator()

    source_text = """
    OpenAI is an artificial intelligence research company.
    This is source text.
    """

    print("\nCalling LLM...\n")

    result = await engine.extract(
        record_type="STARTUP",
        text=source_text,
    )

    print("=" * 60)
    print("RESULT")
    print("=" * 60)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())