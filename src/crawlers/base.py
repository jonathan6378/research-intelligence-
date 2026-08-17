import asyncio
import logging
from typing import Optional

import aiohttp


logger = logging.getLogger(__name__)


class AsyncCrawler:
    def __init__(
        self,
        concurrency: int = 20,
        timeout: int = 30,
    ):
        self.semaphore = asyncio.Semaphore(concurrency)

        self.timeout = aiohttp.ClientTimeout(
            total=timeout
        )

        self.headers = {
            "User-Agent": (
                "FrontierAtlasResearchBot/1.0 "
                "(research data ingestion)"
            )
        }

    async def fetch(
        self,
        session: aiohttp.ClientSession,
        url: str,
    ) -> Optional[str]:

        async with self.semaphore:

            try:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                ) as response:

                    if response.status != 200:
                        logger.warning(
                            "HTTP %s: %s",
                            response.status,
                            url,
                        )
                        return None

                    return await response.text()

            except asyncio.TimeoutError:
                logger.warning(
                    "Timeout: %s",
                    url,
                )
                return None

            except aiohttp.ClientError as exc:
                logger.warning(
                    "Request failed %s: %s",
                    url,
                    exc,
                )
                return None

    async def fetch_many(
        self,
        urls: list[str],
    ) -> dict[str, Optional[str]]:

        async with aiohttp.ClientSession(
            timeout=self.timeout
        ) as session:

            tasks = [
                self.fetch(session, url)
                for url in urls
            ]

            results = await asyncio.gather(
                *tasks,
                return_exceptions=False,
            )

        return dict(zip(urls, results))