import logging
import re

import aiohttp

from src.github.metrics import GitHubClient


logger = logging.getLogger(__name__)


class GitHubDiscovery:

    def __init__(
        self,
        client: GitHubClient,
        minimum_score: float = 55,
    ):

        self.client = client
        self.minimum_score = minimum_score

    async def find_repository(
        self,
        session: aiohttp.ClientSession,
        paper_title: str,
    ):

        query = (
            f'"{paper_title}"'
        )

        candidates = (
            await self.client.search_repositories(
                session,
                query=query,
                limit=5,
            )
        )

        if not candidates:

            return None

        scored = []

        for repo in candidates:

            score = (
                self.client.score_repository(
                    paper_title,
                    repo.get(
                        "name",
                        "",
                    ),
                    repo.get(
                        "description",
                        "",
                    ),
                )
            )

            scored.append(
                (
                    score,
                    repo,
                )
            )

        scored.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        best_score, best_repo = scored[0]

        logger.info(
            "Paper: %s | Repo: %s | Score: %.2f",
            paper_title,
            best_repo.get("full_name"),
            best_score,
        )

        if best_score < self.minimum_score:

            return None

        return {
            "github_url": best_repo.get(
                "html_url"
            ),
            "repository": best_repo.get(
                "full_name"
            ),
            "match_score": round(
                best_score,
                2,
            ),
        }