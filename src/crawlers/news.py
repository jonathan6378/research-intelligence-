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

from src.crawlers.news_sources import (
    NEWS_SOURCES,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


OUTPUT_FILE = Path(
    "data/raw/news.json"
)


async def fetch(
    session,
    url,
):

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
            "Fetch failed for %s: %s",
            url,
            exc,
        )

        return None


def parse_feed(
    xml,
    source_name,
):

    feed = feedparser.parse(
        xml
    )

    articles = []

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

        if not is_within_24_hours(
            published_date
        ):

            logger.info(
                "Skipping old article [%s]: %s",
                source_name,
                title,
            )

            continue

        articles.append(
            {
                "source_name": source_name,
                "title": title,
                "url": url,
                "published_date": (
                    published_date.isoformat()
                    if published_date
                    else None
                ),
            }
        )

    return articles


async def extract_article(
    session,
    article,
):

    html = await fetch(
        session,
        article["url"],
    )

    if not html:

        return None

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    content = ""

    # ------------------------------------------------
    # Method 1: JSON-LD articleBody
    # ------------------------------------------------

    for script in soup.find_all(
        "script",
        type="application/ld+json",
    ):

        try:

            data = json.loads(
                script.string
                or script.get_text()
            )

            candidates = (
                data
                if isinstance(
                    data,
                    list,
                )
                else [data]
            )

            for item in candidates:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                body = item.get(
                    "articleBody"
                )

                if (
                    body
                    and len(body)
                    > len(content)
                ):

                    content = body

        except (
            json.JSONDecodeError,
            TypeError,
        ):

            continue

    # ------------------------------------------------
    # Method 2: HTML selectors
    # ------------------------------------------------

    if len(content) < 200:

        selectors = [
            "article p",
            "[data-testid='article-content'] p",
            ".article-content p",
            ".entry-content p",
            "main p",
        ]

        for selector in selectors:

            paragraphs = [
                p.get_text(
                    " ",
                    strip=True,
                )
                for p in soup.select(
                    selector
                )
            ]

            paragraphs = [
                p
                for p in paragraphs
                if len(p) > 20
            ]

            candidate = "\n".join(
                paragraphs
            )

            if len(candidate) > len(
                content
            ):

                content = candidate

            if len(content) >= 200:

                break

    # ------------------------------------------------
    # Validate
    # ------------------------------------------------

    if len(content.strip()) < 200:

        logger.warning(
            "No usable article text [%s]: %s",
            article["source_name"],
            article["url"],
        )

        return None

    return {
        "schemaVersion": "1.0",
        "recordType": "NEWS",

        "source": {
            "name": article[
                "source_name"
            ],
            "url": article[
                "url"
            ],
        },

        "content": {
            "title": article[
                "title"
            ],
            "text": content.strip(),
            "published_date": article[
                "published_date"
            ],
        },

        "collectedAt": datetime.now(
            timezone.utc
        ).isoformat(),
    }


async def process_source(
    session,
    source,
):

    name = source[
        "name"
    ]

    rss = source[
        "rss"
    ]

    logger.info(
        "========================================"
    )

    logger.info(
        "Processing source: %s",
        name,
    )

    logger.info(
        "RSS: %s",
        rss,
    )

    xml = await fetch(
        session,
        rss,
    )

    if not xml:

        logger.error(
            "Failed RSS: %s",
            name,
        )

        return []

    articles = parse_feed(
        xml,
        name,
    )

    logger.info(
        "%s fresh articles found: %s",
        name,
        len(articles),
    )

    tasks = [
        extract_article(
            session,
            article,
        )
        for article in articles
    ]

    results = await asyncio.gather(
        *tasks
    )

    return [
        result
        for result in results
        if result
    ]


async def main():

    connector = aiohttp.TCPConnector(
        limit=20
    )

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        source_tasks = [
            process_source(
                session,
                source,
            )
            for source in NEWS_SOURCES
        ]

        source_results = await asyncio.gather(
            *source_tasks
        )

    # ------------------------------------------------
    # Flatten
    # ------------------------------------------------

    records = []

    for result in source_results:

        records.extend(
            result
        )

    # ------------------------------------------------
    # Deduplicate by URL
    # ------------------------------------------------

    unique = {}

    for record in records:

        url = record[
            "source"
        ][
            "url"
        ]

        unique[url] = record

    records = list(
        unique.values()
    )

    # ------------------------------------------------
    # Save
    # ------------------------------------------------

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
            records,
            f,
            indent=2,
            ensure_ascii=False,
        )

    # ------------------------------------------------
    # Summary
    # ------------------------------------------------

    logger.info(
        "========================================"
    )

    logger.info(
        "NEWS CRAWL COMPLETE"
    )

    logger.info(
        "Sources: %s",
        len(NEWS_SOURCES),
    )

    logger.info(
        "Final unique records: %s",
        len(records),
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