import asyncio
import aiohttp

from src.github.metrics import GitHubClient


async def main():

    client = GitHubClient()

    async with aiohttp.ClientSession() as session:

        result = await client.get_repository(
            session,
            "huggingface",
            "transformers",
        )

        print(result)


if __name__ == "__main__":
    asyncio.run(main())