import asyncio
import aiohttp

from src.github.metrics import GitHubClient
from src.github.discovery import GitHubDiscovery


async def main():

    client = GitHubClient(
        concurrency=2
    )

    discovery = GitHubDiscovery(
        client,
        minimum_score=55,
    )

    async with aiohttp.ClientSession() as session:

        result = await discovery.find_repository(
            session,
            "Attention Is All You Need",
        )

        print("\nRESULT:")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())