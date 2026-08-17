from src.parsers.date_parser import (
    parse_date,
    is_within_24_hours,
)


tests = [
    "2 hours ago",
    "30 minutes ago",
    "2026-08-15T10:00:00Z",
    "Sat, 15 Aug 2026 10:00:00 GMT",
]


for value in tests:

    parsed = parse_date(value)

    print(
        value,
        "=>",
        parsed,
        "fresh:",
        is_within_24_hours(parsed),
    )