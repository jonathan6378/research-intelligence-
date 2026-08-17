import asyncio
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import aiohttp


ARXIV_API = "https://export.arxiv.org/api/query"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


class ArxivCrawler:

    def __init__(
        self,
        concurrency: int = 3,
        page_size: int = 100,
    ):
        self.semaphore = asyncio.Semaphore(concurrency)
        self.page_size = page_size

    async def search(
        self,
        session: aiohttp.ClientSession,
        start: int = 0,
        max_results: int = 100,
    ) -> List[dict]:

        params = {
            "search_query": "cat:cs.AI",
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        async with self.semaphore:

            logger.info(
                "Fetching arXiv records %s → %s",
                start,
                start + max_results,
            )

            try:

                async with session.get(
                    ARXIV_API,
                    params=params,
                    timeout=60,
                ) as response:

                    response.raise_for_status()

                    xml_data = await response.text()

                    return self._parse(xml_data)

            except Exception as exc:

                logger.error(
                    "Failed to fetch start=%s: %s",
                    start,
                    exc,
                )

                return []

    def _parse(
        self,
        xml_data: str,
    ) -> List[dict]:

        root = ET.fromstring(xml_data)

        namespace = {
            "atom": "http://www.w3.org/2005/Atom"
        }

        papers = []

        for entry in root.findall(
            "atom:entry",
            namespace,
        ):

            title = entry.find(
                "atom:title",
                namespace,
            )

            published = entry.find(
                "atom:published",
                namespace,
            )

            updated = entry.find(
                "atom:updated",
                namespace,
            )

            summary = entry.find(
                "atom:summary",
                namespace,
            )

            paper_url = entry.find(
                "atom:id",
                namespace,
            )

            if title is None or paper_url is None:
                continue

            authors = []

            for author in entry.findall(
                "atom:author",
                namespace,
            ):

                name = author.find(
                    "atom:name",
                    namespace,
                )

                if name is not None and name.text:
                    authors.append(
                        name.text.strip()
                    )

            published_date = None

            if published is not None and published.text:

                published_date = datetime.fromisoformat(
                    published.text.replace(
                        "Z",
                        "+00:00",
                    )
                )

            updated_date = None

            if updated is not None and updated.text:

                updated_date = datetime.fromisoformat(
                    updated.text.replace(
                        "Z",
                        "+00:00",
                    )
                )

            papers.append(
                {
                    "title": " ".join(
                        title.text.split()
                    ),
                    "authors": authors,
                    "paper_url": paper_url.text.strip(),
                    "published_date": (
                        published_date.isoformat()
                        if published_date
                        else None
                    ),
                    "updated_date": (
                        updated_date.isoformat()
                        if updated_date
                        else None
                    ),
                    "summary": (
                        " ".join(
                            summary.text.split()
                        )
                        if summary is not None
                        and summary.text
                        else ""
                    ),
                    "source": {
                        "name": "arXiv",
                        "url": paper_url.text.strip(),
                    },
                    "collected_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )

        return papers

    async def collect(
        self,
        session: aiohttp.ClientSession,
        total: int = 1000,
    ) -> List[dict]:

        tasks = []

        for start in range(
            0,
            total,
            self.page_size,
        ):

            tasks.append(
                self.search(
                    session=session,
                    start=start,
                    max_results=min(
                        self.page_size,
                        total - start,
                    ),
                )
            )

        results = await asyncio.gather(
            *tasks
        )

        papers = []

        for batch in results:
            papers.extend(batch)

        # Deduplicate using paper URL
        unique = {}

        for paper in papers:

            url = paper["paper_url"]

            if url not in unique:
                unique[url] = paper

        papers = list(unique.values())

        logger.info(
            "Collected %s unique papers",
            len(papers),
        )

        return papers


async def main():

    crawler = ArxivCrawler(
        concurrency=3,
        page_size=100,
    )

    timeout = aiohttp.ClientTimeout(
        total=120
    )

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        papers = await crawler.collect(
            session,
            total=1000,
        )

    output_dir = Path("data/raw")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_dir / "research_papers.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            papers,
            f,
            indent=2,
            ensure_ascii=False,
        )

    logger.info(
        "Saved dataset to %s",
        output_file,
    )


if __name__ == "__main__":
    asyncio.run(main())