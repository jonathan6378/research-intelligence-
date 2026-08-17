from src.validation import validate_research_paper


valid_record = {
    "schemaVersion": "1.0",
    "recordType": "RESEARCH_PAPER",
    "content": {
        "title": "Test Paper",
        "authors": ["Author"],
        "paper_url": "https://arxiv.org/abs/test",
        "github_url": None,
        "github_stars": None,
        "published_date": "2026-08-15T10:00:00+00:00",
    },
}


invalid_record = {
    "schemaVersion": "1.0",
    "recordType": "RESEARCH_PAPER",
    "content": {
        "title": "Test Paper",
    },
}


print("=" * 60)
print("VALID RECORD")
print("=" * 60)

ok, errors = validate_research_paper(valid_record)

print("Valid:", ok)
print("Errors:", errors)


print("\n" + "=" * 60)
print("INVALID RECORD")
print("=" * 60)

ok, errors = validate_research_paper(invalid_record)

print("Valid:", ok)
print("Errors:", errors)