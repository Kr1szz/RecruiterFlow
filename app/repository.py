from collections.abc import Iterable
from typing import Any

import psycopg

CANDIDATE_SELECT = """
    SELECT c.id, c.name, c.experience_years, c.availability,
           ARRAY(SELECT s.name FROM candidate_skills AS cs
                 JOIN skills AS s ON s.id = cs.skill_id
                 WHERE cs.candidate_id = c.id ORDER BY s.name) AS skills,
           ARRAY(SELECT t.name FROM candidate_traits AS ct
                 JOIN traits AS t ON t.id = ct.trait_id
                 WHERE ct.candidate_id = c.id ORDER BY t.name) AS traits
    FROM candidates AS c"""

JOB_SELECT = """
    SELECT j.id, j.title, j.min_experience,
           ARRAY(SELECT s.name FROM job_skills AS js
                 JOIN skills AS s ON s.id = js.skill_id
                 WHERE js.job_id = j.id ORDER BY s.name) AS required_skills,
           ARRAY(SELECT t.name FROM job_culture AS jc
                 JOIN traits AS t ON t.id = jc.trait_id
                 WHERE jc.job_id = j.id ORDER BY t.name) AS culture
    FROM jobs AS j"""


def link_names(
    connection: psycopg.Connection, lookup: str, link: str, owner_column: str, owner_id: int, names: Iterable[str]
) -> None:
    """Upsert names into a lookup table (skills/traits) and link them to one owner row.

    Table and column names are only ever the fixed literals passed below, never input.
    """
    connection.execute(
        f"""WITH names AS (SELECT DISTINCT unnest(%(names)s::text[]) AS name),
                 ids AS (INSERT INTO {lookup} (name) SELECT name FROM names
                         ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                         RETURNING id)
            INSERT INTO {link} ({owner_column}, {lookup[:-1]}_id)
            SELECT %(owner_id)s, id FROM ids""",
        {"names": list(names), "owner_id": owner_id},
    )


class RecruiterRepository:
    def __init__(self, connection: psycopg.Connection):
        self.connection = connection

    def get_job(self, job_id: int) -> dict[str, Any] | None:
        return self.connection.execute(JOB_SELECT + " WHERE j.id = %s", (job_id,)).fetchone()

    def get_candidate(self, candidate_id: int) -> dict[str, Any] | None:
        return self.connection.execute(CANDIDATE_SELECT + " WHERE c.id = %s", (candidate_id,)).fetchone()

    def list_candidates(self) -> list[dict[str, Any]]:
        return self.connection.execute(CANDIDATE_SELECT).fetchall()

    def list_jobs(self) -> list[dict[str, Any]]:
        return self.connection.execute(JOB_SELECT).fetchall()

    def create_candidate(
        self,
        name: str,
        skills: Iterable[str],
        experience_years: int,
        availability: str,
        traits: Iterable[str],
        quirk: str,
    ) -> int:
        candidate_id = self.connection.execute(
            """INSERT INTO candidates (name, experience_years, availability, quirk)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (name, experience_years, availability, quirk),
        ).fetchone()["id"]
        link_names(self.connection, "skills", "candidate_skills", "candidate_id", candidate_id, skills)
        link_names(self.connection, "traits", "candidate_traits", "candidate_id", candidate_id, traits)
        return candidate_id

    def create_job(
        self, title: str, required_skills: Iterable[str], min_experience: int, culture: Iterable[str], tagline: str
    ) -> int:
        job_id = self.connection.execute(
            "INSERT INTO jobs (title, min_experience, tagline) VALUES (%s, %s, %s) RETURNING id",
            (title, min_experience, tagline),
        ).fetchone()["id"]
        link_names(self.connection, "skills", "job_skills", "job_id", job_id, required_skills)
        link_names(self.connection, "traits", "job_culture", "job_id", job_id, culture)
        return job_id
