import feedparser

from src.crawlers.news_sources import NEWS_SOURCES


for source in NEWS_SOURCES:

    print("\n" + "=" * 60)

    print(source["name"])

    print(source["rss"])

    feed = feedparser.parse(
        source["rss"]
    )

    print(
        "Entries:",
        len(feed.entries)
    )

    if feed.entries:

        first = feed.entries[0]

        print(
            "First:",
            first.get("title")
        )

        print(
            "Date:",
            first.get("published")
            or first.get("updated")
        )