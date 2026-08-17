import asyncio
import logging
import os
import random
from typing import Optional

import aiohttp
from dotenv import load_dotenv
from rapidfuzz import fuzz


load_dotenv()

logger = logging.getLogger(__name__)


class GitHubClient:

    API_URL = "https://api.github.com"

    def __init__(
        self,
        concurrency: int = 5,
        max_retries: int = 5,
    ):

        self.semaphore = asyncio.Semaphore(
            concurrency
        )

        self.max_retries = max_retries

        self.token = os.getenv(
            "GITHUB_TOKEN"
        )

        self.headers = {
            "Accept": (
                "application/vnd.github+json"
            ),
            "User-Agent": (
                "FrontierAtlasResearchBot"
            ),
        }

        if self.token:
            self.headers[
                "Authorization"
            ] = f"Bearer {self.token}"

    async def _request(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: Optional[dict] = None,
    ):

        for attempt in range(
            self.max_retries
        ):

            try:

                async with self.semaphore:

                    async with session.get(
                        url,
                        headers=self.headers,
                        params=params,
                        timeout=30,
                    ) as response:

                        if response.status == 200:

                            return await response.json()

                        if response.status == 404:

                            return None

                        if response.status == 429:

                            retry_after = (
                                response.headers.get(
                                    "Retry-After"
                                )
                            )

                            if retry_after:

                                delay = float(
                                    retry_after
                                )

                            else:

                                delay = min(
                                    2 ** attempt,
                                    60,
                                )

                            logger.warning(
                                "GitHub rate limited. "
                                "Waiting %.1fs",
                                delay,
                            )

                            await asyncio.sleep(
                                delay
                                + random.uniform(
                                    0,
                                    1,
                                )
                            )

                            continue

                        if response.status in {
                            500,
                            502,
                            503,
                            504,
                        }:

                            delay = min(
                                2 ** attempt,
                                60,
                            )

                            logger.warning(
                                "GitHub HTTP %s. "
                                "Retrying in %.1fs",
                                response.status,
                                delay,
                            )

                            await asyncio.sleep(
                                delay
                                + random.uniform(
                                    0,
                                    1,
                                )
                            )

                            continue

                        logger.warning(
                            "GitHub HTTP %s: %s",
                            response.status,
                            url,
                        )

                        return None

            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
            ) as exc:

                delay = min(
                    2 ** attempt,
                    60,
                )

                logger.warning(
                    "GitHub request failed: %s. "
                    "Retrying in %.1fs",
                    exc,
                    delay,
                )

                await asyncio.sleep(
                    delay
                    + random.uniform(
                        0,
                        1,
                    )
                )

        logger.error(
            "GitHub request permanently failed: %s",
            url,
        )

        return None

    async def search_repositories(
        self,
        session: aiohttp.ClientSession,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        url = (
            f"{self.API_URL}/search/repositories"
        )

        params = {
            "q": query,
            "per_page": limit,
        }

        return (
            await self._request(
                session,
                url,
                params,
            )
            or {}
        ).get("items", [])

    async def get_repository(
        self,
        session: aiohttp.ClientSession,
        owner: str,
        repo: str,
    ) -> Optional[dict]:

        url = (
            f"{self.API_URL}/repos/"
            f"{owner}/{repo}"
        )

        data = await self._request(
            session,
            url,
        )

        if not data:
            return None

        return {
            "github_url": data.get(
                "html_url"
            ),
            "github_stars": data.get(
                "stargazers_count",
                0,
            ),
            "github_forks": data.get(
                "forks_count",
                0,
            ),
            "github_updated_at": data.get(
                "updated_at"
            ),
        }

    @staticmethod
    def score_repository(
        paper_title: str,
        repository_name: str,
        description: Optional[str],
    ) -> float:

        title = paper_title.lower()

        repo_name = (
            repository_name
            .replace("-", " ")
            .replace("_", " ")
            .lower()
        )

        score_name = fuzz.token_set_ratio(
            title,
            repo_name,
        )

        score_description = 0

        if description:

            score_description = (
                fuzz.token_set_ratio(
                    title,
                    description.lower(),
                )
            )

        return (
            score_name * 0.7
            + score_description * 0.3
        )