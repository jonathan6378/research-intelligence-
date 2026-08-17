from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import re


RELATIVE_PATTERN = re.compile(
    r"(\d+)\s+(minute|minutes|hour|hours|day|days)\s+ago",
    re.IGNORECASE,
)


def parse_date(value: str | None):
    """
    Convert common publication date formats
    into timezone-aware UTC datetime.
    """

    if not value:
        return None

    value = value.strip()

    # ---------------------------------------------
    # Relative dates
    # ---------------------------------------------

    match = RELATIVE_PATTERN.search(value)

    if match:

        amount = int(
            match.group(1)
        )

        unit = (
            match.group(2)
            .lower()
        )

        now = datetime.now(
            timezone.utc
        )

        if "minute" in unit:

            return now - timedelta(
                minutes=amount
            )

        if "hour" in unit:

            return now - timedelta(
                hours=amount
            )

        if "day" in unit:

            return now - timedelta(
                days=amount
            )

    # ---------------------------------------------
    # ISO format
    # ---------------------------------------------

    try:

        parsed = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )

    except ValueError:
        pass

    # ---------------------------------------------
    # HTTP / RSS dates
    # ---------------------------------------------

    try:

        parsed = parsedate_to_datetime(
            value
        )

        if parsed.tzinfo is None:

            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )

    except (TypeError, ValueError):

        return None


def is_within_24_hours(
    published_at: datetime | None,
) -> bool:

    if published_at is None:

        return False

    now = datetime.now(
        timezone.utc
    )

    age = (
        now - published_at
    )

    return timedelta(
        hours=0
    ) <= age <= timedelta(
        hours=24
    )