from datetime import datetime


def validate_research_paper(record: dict) -> tuple[bool, list[str]]:
    errors = []

    if record.get("schemaVersion") != "1.0":
        errors.append("Invalid schemaVersion")

    if record.get("recordType") != "RESEARCH_PAPER":
        errors.append("Invalid recordType")

    content = record.get("content")

    if not isinstance(content, dict):
        errors.append("Missing content object")
        return False, errors

    required = [
        "title",
        "authors",
        "paper_url",
        "github_url",
        "github_stars",
        "published_date",
    ]

    for field in required:
        if field not in content:
            errors.append(f"Missing field: {field}")

    if "authors" in content and not isinstance(content["authors"], list):
        errors.append("authors must be an array")

    if content.get("github_stars") is not None:
        if not isinstance(content["github_stars"], int):
            errors.append("github_stars must be integer or null")

    if content.get("paper_url") is not None:
        if not isinstance(content["paper_url"], str):
            errors.append("paper_url must be string or null")

    if content.get("published_date") is not None:
        try:
            datetime.fromisoformat(
                content["published_date"].replace("Z", "+00:00")
            )
        except ValueError:
            errors.append("Invalid published_date")

    return len(errors) == 0, errors