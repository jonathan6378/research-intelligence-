import feedparser

from src.crawlers.job_sources import JOB_SOURCES


for source in JOB_SOURCES:

    if source["type"] != "rss":
        continue

    print("\n" + "=" * 60)

    print(source["name"])
    print(source["url"])

    feed = feedparser.parse(
        source["url"]
    )

    print(
        "Entries:",
        len(feed.entries)
    )

    for entry in feed.entries[:3]:

        print(
            "TITLE:",
            entry.get("title")
        )

        print(
            "DATE:",
            entry.get("published")
            or entry.get("updated")
        )

        print(
            "URL:",
            entry.get("link")
        )