"""Rebuild the Recruiter Bot schema and load the assignment's candidate and job data."""

import json
from pathlib import Path

from app.db import get_connection
from app.repository import RecruiterRepository

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
SEED_PATH = ROOT / "data" / "seed_data.json"


def seed() -> None:
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    with get_connection() as connection:
        connection.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
        repository = RecruiterRepository(connection)
        for candidate in data["candidates"]:
            repository.create_candidate(**candidate)
        for job in data["jobs"]:
            repository.create_job(**job)
    print(f"Seeded {len(data['candidates'])} candidates and {len(data['jobs'])} jobs.")


if __name__ == "__main__":
    seed()
