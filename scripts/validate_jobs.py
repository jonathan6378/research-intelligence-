import json
from datetime import datetime, timezone


FILE = "data/raw/jobs.json"


with open(
    FILE,
    encoding="utf-8"
) as f:
    jobs = json.load(f)


print("=" * 60)
print("JOB DATA VALIDATION")
print("=" * 60)

print("Total jobs:", len(jobs))


required = [
    "schemaVersion",
    "recordType",
    "source",
    "content",
    "collectedAt",
]


errors = 0


for i, job in enumerate(jobs):

    # Top-level fields

    for field in required:

        if field not in job:

            print(
                f"ERROR [{i}]: "
                f"missing {field}"
            )

            errors += 1


    if job.get("recordType") != "JOB":

        print(
            f"ERROR [{i}]: "
            "recordType is not JOB"
        )

        errors += 1


    content = job.get(
        "content",
        {}
    )

    required_content = [
        "company",
        "date",
        "is_remote",
        "role_family",
        "title",
    ]


    for field in required_content:

        if field not in content:

            print(
                f"ERROR [{i}]: "
                f"missing content.{field}"
            )

            errors += 1


    # Validate timestamp

    try:

        date = datetime.fromisoformat(
            content["date"]
        )

        if date.tzinfo is None:

            print(
                f"ERROR [{i}]: "
                "date has no timezone"
            )

            errors += 1

    except Exception:

        print(
            f"ERROR [{i}]: "
            "invalid date"
        )

        errors += 1


print("=" * 60)

if errors == 0:

    print("VALIDATION PASSED ✅")

else:

    print(
        "VALIDATION FAILED ❌"
    )

    print(
        "Errors:",
        errors
    )

print("=" * 60)