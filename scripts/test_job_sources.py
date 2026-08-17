import asyncio
import aiohttp

from src.crawlers.job_sources import (
    JOB_SOURCES,
)


async def fetch(
    session,
    source,
):

    try:

        async with session.get(
            source["url"],
            timeout=30,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/142.0 Safari/537.36"
                )
            },
        ) as response:

            print(
                "\n"
                + "=" * 60
            )

            print(
                source["name"]
            )

            print(
                source["url"]
            )

            print(
                "HTTP:",
                response.status,
            )

            text = await response.text()

            print(
                "HTML length:",
                len(text),
            )

            return text

    except Exception as exc:

        print(
            "ERROR:",
            exc,
        )


async def main():

    async with aiohttp.ClientSession() as session:

        tasks = [
            fetch(
                session,
                source,
            )
            for source in JOB_SOURCES
        ]

        await asyncio.gather(
            *tasks
        )


if __name__ == "__main__":

    asyncio.run(main())