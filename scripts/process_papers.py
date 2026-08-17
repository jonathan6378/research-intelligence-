
import asyncio
import json
import logging
from pathlib import Path

from src.llm.orchestrator import LLMOrchestrator
from src.merge import build_research_paper
from src.validation import validate_research_paper


INPUT_FILE = Path("data/raw/research_papers_enriched.json")
OUTPUT_FILE = Path("data/processed/research_papers_final.json")
CHECKPOINT_FILE = Path("data/processed/research_papers_checkpoint.json")

CONCURRENCY = 2
CHECKPOINT_EVERY = 10


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


async def process_one(paper, engine, semaphore, index):
    async with semaphore:
        try:
            source_text = json.dumps(
                paper,
                ensure_ascii=False,
                indent=2,
            )

            result = await engine.extract(
                record_type="RESEARCH_PAPER",
                text=source_text,
            )

            llm_data = result.get("data", {})

            final_record = build_research_paper(
                paper,
                llm_data,
            )

            valid, errors = validate_research_paper(
                final_record
            )

            if not valid:
                logger.error(
                    "Validation failed [%d] %s: %s",
                    index,
                    paper.get("title"),
                    errors,
                )
                return index, None

            return index, final_record

        except Exception as exc:
            logger.error(
                "Failed [%d]: %s | %s",
                index,
                paper.get("title"),
                exc,
            )
            return index, None


def load_checkpoint():
    if not CHECKPOINT_FILE.exists():
        return {}

    try:
        with open(
            CHECKPOINT_FILE,
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        # Old checkpoint format: list
        if isinstance(data, list):
            logger.warning(
                "Old checkpoint format detected."
            )

            converted = {}

            for i, record in enumerate(data):
                converted[i] = record

            return converted

        # New checkpoint format
        if isinstance(data, dict):
            return {
                int(k): v
                for k, v in data.items()
            }

        return {}

    except Exception as exc:
        logger.error(
            "Could not load checkpoint: %s",
            exc,
        )
        return {}


def save_checkpoint(results):
    CHECKPOINT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ordered = {
        str(index): results[index]
        for index in sorted(results)
    }

    with open(
        CHECKPOINT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            ordered,
            f,
            indent=2,
            ensure_ascii=False,
        )


def save_final(results):
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ordered = [
        results[index]
        for index in sorted(results)
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            ordered,
            f,
            indent=2,
            ensure_ascii=False,
        )


async def main():

    # --------------------------------------------------
    # Load input
    # --------------------------------------------------

    with open(
        INPUT_FILE,
        encoding="utf-8",
    ) as f:
        papers = json.load(f)

    logger.info(
        "Loaded %d papers",
        len(papers),
    )

    # --------------------------------------------------
    # Load checkpoint
    # --------------------------------------------------

    results = load_checkpoint()

    logger.info(
        "Checkpoint contains %d successful records",
        len(results),
    )

    # --------------------------------------------------
    # Find papers that still need processing
    # --------------------------------------------------

    remaining = [
        (index, paper)
        for index, paper in enumerate(papers)
        if index not in results
    ]

    logger.info(
        "Papers remaining: %d",
        len(remaining),
    )

    if not remaining:
        logger.info(
            "All papers already processed."
        )

        save_final(results)
        return

    # --------------------------------------------------
    # LLM engine
    # --------------------------------------------------

    engine = LLMOrchestrator()

    semaphore = asyncio.Semaphore(
        CONCURRENCY
    )

    # --------------------------------------------------
    # Process in small batches
    # --------------------------------------------------

    for batch_start in range(
        0,
        len(remaining),
        CHECKPOINT_EVERY,
    ):

        batch = remaining[
            batch_start:
            batch_start + CHECKPOINT_EVERY
        ]

        logger.info("=" * 60)

        logger.info(
            "Processing papers %d-%d",
            batch[0][0],
            batch[-1][0],
        )

        tasks = [
            process_one(
                paper,
                engine,
                semaphore,
                index,
            )
            for index, paper in batch
        ]

        batch_results = await asyncio.gather(
            *tasks
        )

        successful = 0

        for index, result in batch_results:

            if result is not None:
                results[index] = result
                successful += 1

        save_checkpoint(results)

        logger.info(
            "Checkpoint saved: %d/%d",
            len(results),
            len(papers),
        )

        logger.info(
            "Successful in this batch: %d/%d",
            successful,
            len(batch),
        )

        # Small pause between batches
        await asyncio.sleep(2)

    # --------------------------------------------------
    # Save final
    # --------------------------------------------------

    save_final(results)

    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info(
        "Input papers: %d",
        len(papers),
    )
    logger.info(
        "Valid output: %d",
        len(results),
    )
    logger.info(
        "Saved: %s",
        OUTPUT_FILE,
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning(
            "Process interrupted by user."
        )