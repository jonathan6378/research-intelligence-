import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from src.parsers.date_parser import (
    parse_date,
    is_within_24_hours,
)

from src.crawlers.job_sources import (
    JOB_SOURCES,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

OUTPUT_FILE = Path(
    "data/raw/jobs.json"
)


async def fetch(session, url):

    try:

        async with session.get(
            url,
            timeout=30,
            headers={
                "User-Agent": (
                    "FrontierAtlasDemo/1.0"
                )
            },
        ) as response:

            if response.status != 200:

                logger.warning(
                    "HTTP %s: %s",
                    response.status,
                    url,
                )

                return None

            return await response.text()

    except Exception as exc:

        logger.warning(
            "Fetch failed: %s | %s",
            url,
            exc,
        )

        return None


def role_family(title):

    title_lower = title.lower()

    if any(
        x in title_lower
        for x in [
            "engineer",
            "developer",
            "software",
            "machine learning",
            "ml engineer",
            "ai engineer",
        ]
    ):
        return "Engineering"

    if any(
        x in title_lower
        for x in [
            "data scientist",
            "data science",
            "data analyst",
        ]
    ):
        return "Data"

    if any(
        x in title_lower
        for x in [
            "research",
            "scientist",
        ]
    ):
        return "Research"

    if any(
        x in title_lower
        for x in [
            "product",
            "product manager",
        ]
    ):
        return "Product"

    if any(
        x in title_lower
        for x in [
            "designer",
            "design",
        ]
    ):
        return "Design"

    if any(
        x in title_lower
        for x in [
            "marketing",
            "growth",
        ]
    ):
        return "Marketing"

    return "Other"


def detect_remote(text):

    text = text.lower()

    remote_terms = [
        "remote",
        "work from home",
        "fully remote",
        "remote-friendly",
        "distributed team",
    ]

    return any(
        term in text
        for term in remote_terms
    )


def extract_company(title):

    parts = [
        part.strip()
        for part in title.split("·")
    ]

    if len(parts) >= 2:

        return parts[1]

    if " at " in title.lower():

        parts = title.split(
            " at ",
            1,
        )

        if len(parts) == 2:

            return parts[1].strip()

    return "Unknown"


def parse_rss_jobs(
    xml,
    source_name,
):

    feed = feedparser.parse(
        xml
    )

    jobs = []

    for entry in feed.entries:

        title = entry.get(
            "title"
        )

        url = entry.get(
            "link"
        )

        published = (
            entry.get("published")
            or entry.get("updated")
        )

        if not title or not url:

            continue

        published_date = parse_date(
            published
        )

        if not published_date:

            logger.warning(
                "No date: %s",
                title,
            )

            continue

        if not is_within_24_hours(
            published_date
        ):

            logger.info(
                "Skipping old job [%s]: %s",
                source_name,
                title,
            )

            continue

        description = (
            entry.get(
                "summary"
            )
            or entry.get(
                "description"
            )
            or ""
        )

        description = BeautifulSoup(
            description,
            "html.parser",
        ).get_text(
            " ",
            strip=True,
        )

        combined_text = (
            title
            + " "
            + description
        )

        jobs.append(
            {
                "schemaVersion": "1.0",
                "recordType": "JOB",

                "source": {
                    "name": source_name,
                    "url": url,
                },

                "content": {
                    "company": extract_company(
                        title
                    ),

                    "date": (
                        published_date.isoformat()
                    ),

                    "is_remote": detect_remote(
                        combined_text
                    ),

                    "role_family": role_family(
                        title
                    ),

                    "title": title,
                },

                "collectedAt": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
            }
        )

    return jobs


async def process_source(
    session,
    source,
):

    logger.info(
        "Processing job source: %s",
        source["name"],
    )

    if source["type"] != "rss":

        logger.info(
            "HTML source deferred: %s",
            source["name"],
        )

        return []

    xml = await fetch(
        session,
        source["url"],
    )

    if not xml:

        return []

    jobs = parse_rss_jobs(
        xml,
        source["name"],
    )

    logger.info(
        "%s fresh jobs: %s",
        source["name"],
        len(jobs),
    )

    return jobs


async def main():

    connector = aiohttp.TCPConnector(
        limit=20
    )

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        tasks = [
            process_source(
                session,
                source,
            )
            for source in JOB_SOURCES
        ]

        results = await asyncio.gather(
            *tasks
        )

    jobs = []

    for result in results:

        jobs.extend(
            result
        )

    # URL deduplication

    unique = {}

    for job in jobs:

        url = job[
            "source"
        ][
            "url"
        ]

        unique[url] = job

    jobs = list(
        unique.values()
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            jobs,
            f,
            indent=2,
            ensure_ascii=False,
        )

    logger.info(
        "========================================"
    )

    logger.info(
        "JOB CRAWL COMPLETE"
    )

    logger.info(
        "Total fresh jobs: %s",
        len(jobs),
    )

    logger.info(
        "Saved: %s",
        OUTPUT_FILE,
    )

    logger.info(
        "========================================"
    )


if __name__ == "__main__":

    asyncio.run(main())