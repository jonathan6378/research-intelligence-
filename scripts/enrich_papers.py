import asyncio
import json
import logging
from pathlib import Path

import aiohttp

from src.github.discovery import GitHubDiscovery
from src.github.metrics import GitHubClient


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


INPUT_FILE = Path(
    "data/raw/research_papers.json"
)

OUTPUT_FILE = Path(
    "data/raw/research_papers_enriched.json"
)

CHECKPOINT_FILE = Path(
    "data/raw/research_papers_checkpoint.json"
)

BATCH_SIZE = 25


def save_checkpoint(papers):
    """Safely save current progress."""

    temp_file = CHECKPOINT_FILE.with_suffix(
        ".tmp"
    )

    with open(
        temp_file,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            papers,
            f,
            indent=2,
            ensure_ascii=False,
        )

    temp_file.replace(
        CHECKPOINT_FILE
    )


async def enrich_paper(
    paper,
    discovery,
    session,
):

    title = paper.get(
        "title",
        "",
    )

    logger.info(
        "Processing: %s",
        title,
    )

    try:

        result = (
            await discovery.find_repository(
                session,
                title,
            )
        )

        if result is None:

            paper["github_url"] = None
            paper["github_stars"] = None
            paper["github_forks"] = None
            paper["github_match_score"] = None

            return paper

        repository = result[
            "repository"
        ]

        owner, repo = repository.split(
            "/",
            1,
        )

        metrics = (
            await discovery.client.get_repository(
                session,
                owner,
                repo,
            )
        )

        paper["github_url"] = (
            result["github_url"]
        )

        paper["github_match_score"] = (
            result["match_score"]
        )

        if metrics:

            paper["github_stars"] = (
                metrics["github_stars"]
            )

            paper["github_forks"] = (
                metrics["github_forks"]
            )

            paper["github_updated_at"] = (
                metrics["github_updated_at"]
            )

        else:

            paper["github_stars"] = None
            paper["github_forks"] = None
            paper["github_updated_at"] = None

        return paper

    except Exception as exc:

        logger.exception(
            "Failed to process paper: %s",
            title,
        )

        paper["github_error"] = str(
            exc
        )

        return paper


async def main():

    # -------------------------------------------------
    # Load original papers
    # -------------------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        papers = json.load(f)

    logger.info(
        "Loaded %s papers",
        len(papers),
    )

    # -------------------------------------------------
    # Load checkpoint if available
    # -------------------------------------------------

    if CHECKPOINT_FILE.exists():

        logger.info(
            "Checkpoint found. Resuming..."
        )

        with open(
            CHECKPOINT_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            papers = json.load(f)

    else:

        logger.info(
            "No checkpoint found. Starting fresh."
        )

    # -------------------------------------------------
    # GitHub configuration
    # -------------------------------------------------

    client = GitHubClient(
        concurrency=3,
        max_retries=5,
    )

    discovery = GitHubDiscovery(
        client,
        minimum_score=55,
    )

    timeout = aiohttp.ClientTimeout(
        total=60,
    )

    connector = aiohttp.TCPConnector(
        limit=10,
    )

    # -------------------------------------------------
    # Process papers
    # -------------------------------------------------

    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
    ) as session:

        for start in range(
            0,
            len(papers),
            BATCH_SIZE,
        ):

            end = min(
                start + BATCH_SIZE,
                len(papers),
            )

            batch = papers[
                start:end
            ]

            # Skip papers already processed
            pending = [
                paper
                for paper in batch
                if "github_url" not in paper
            ]

            if not pending:

                logger.info(
                    "Batch %s-%s already processed",
                    start,
                    end,
                )

                continue

            logger.info(
                "Processing batch %s-%s",
                start,
                end,
            )

            tasks = [
                enrich_paper(
                    paper,
                    discovery,
                    session,
                )
                for paper in pending
            ]

            await asyncio.gather(
                *tasks
            )

            # -----------------------------------------
            # Save checkpoint
            # -----------------------------------------

            save_checkpoint(
                papers
            )

            logger.info(
                "Checkpoint saved: %s/%s",
                end,
                len(papers),
            )

    # -------------------------------------------------
    # Save final dataset
    # -------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            papers,
            f,
            indent=2,
            ensure_ascii=False,
        )

    matched = sum(
        1
        for paper in papers
        if paper.get("github_url")
    )

    logger.info(
        "================================"
    )

    logger.info(
        "ENRICHMENT COMPLETE"
    )

    logger.info(
        "Total papers: %s",
        len(papers),
    )

    logger.info(
        "GitHub matches: %s",
        matched,
    )

    logger.info(
        "No GitHub match: %s",
        len(papers) - matched,
    )

    logger.info(
        "Saved: %s",
        OUTPUT_FILE,
    )

    logger.info(
        "================================"
    )


if __name__ == "__main__":
    asyncio.run(main())