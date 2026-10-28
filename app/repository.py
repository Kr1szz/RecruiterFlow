from typing import Any

import psycopg


class RecruiterRepository:
    def __init__(self, connection: psycopg.Connection):
        self.connection = connection

    def get_job(self, job_id: int) -> dict[str, Any] | None:
        return self.connection.execute(
            """SELECT j.id, j.title, j.min_experience,
                      COALESCE(array_agg(js.skill ORDER BY js.skill)
                               FILTER (WHERE js.skill IS NOT NULL), ARRAY[]::text[]) AS required_skills
               FROM jobs AS j
               LEFT JOIN job_required_skills AS js ON js.job_id = j.id
               WHERE j.id = %s
               GROUP BY j.id, j.title, j.min_experience""",
            (job_id,),
        ).fetchone()

    def get_candidate(self, candidate_id: int) -> dict[str, Any] | None:
        return self.connection.execute(
            """SELECT c.id, c.name, c.experience_years,
                      COALESCE(array_agg(cs.skill ORDER BY cs.skill)
                               FILTER (WHERE cs.skill IS NOT NULL), ARRAY[]::text[]) AS skills
               FROM candidates AS c
               LEFT JOIN candidate_skills AS cs ON cs.candidate_id = c.id
               WHERE c.id = %s
               GROUP BY c.id, c.name, c.experience_years""",
            (candidate_id,),
        ).fetchone()

    def list_candidates(self) -> list[dict[str, Any]]:
        return self.connection.execute(
            """SELECT c.id, c.name, c.experience_years,
                      COALESCE(array_agg(cs.skill ORDER BY cs.skill)
                               FILTER (WHERE cs.skill IS NOT NULL), ARRAY[]::text[]) AS skills
               FROM candidates AS c
               LEFT JOIN candidate_skills AS cs ON cs.candidate_id = c.id
               GROUP BY c.id, c.name, c.experience_years"""
        ).fetchall()

    def list_jobs(self) -> list[dict[str, Any]]:
        return self.connection.execute(
            """SELECT j.id, j.title, j.min_experience,
                      COALESCE(array_agg(js.skill ORDER BY js.skill)
                               FILTER (WHERE js.skill IS NOT NULL), ARRAY[]::text[]) AS required_skills
               FROM jobs AS j
               LEFT JOIN job_required_skills AS js ON js.job_id = j.id
               GROUP BY j.id, j.title, j.min_experience"""
        ).fetchall()

