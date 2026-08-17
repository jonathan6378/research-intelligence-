from datetime import datetime, timezone


def build_research_paper(raw: dict, llm: dict) -> dict:

    content = {
        # Deterministic crawler data takes priority
        "title": raw.get("title"),

        "authors": raw.get("authors", []),

        "paper_url": raw.get("paper_url"),

        "github_url": raw.get("github_url"),

        "github_stars": raw.get("github_stars"),

        "published_date": raw.get("published_date"),
    }

    # LLM may provide a summary,
    # but it cannot overwrite trusted metadata.
    if llm.get("summary") is not None:
        content["summary"] = llm["summary"]

    return {
        "schemaVersion": "1.0",
        "recordType": "RESEARCH_PAPER",

        "source": {
            "name": raw.get("source", {}).get("name", "arXiv"),
            "url": raw.get("paper_url"),
        },

        "content": content,

        "collectedAt": raw.get(
            "collected_at",
            datetime.now(timezone.utc).isoformat(),
        ),
    }