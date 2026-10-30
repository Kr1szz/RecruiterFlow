"""End-to-end check against a real PostgreSQL database (DATABASE_URL).

Exercises schema.sql, the seed and the handwritten queries. Skipped when no
database is reachable. Note: seeding rebuilds the schema in that database.
"""

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.db import database_url
from app.main import app
from app.seed import seed


@pytest.fixture(scope="module")
def client():
    try:
        psycopg.connect(database_url(), connect_timeout=2).close()
    except psycopg.OperationalError:
        pytest.skip("PostgreSQL is not reachable at DATABASE_URL")
    seed()
    yield TestClient(app)
    seed()  # leave the seed data as it was, without the rows these tests create


def test_job_matches_rank_every_candidate(client):
    body = client.get("/jobs/1/matches").json()

    assert len(body["matches"]) == 15
    assert body["matches"][0]["name"] == "Sherlock H."
    scores = [match["score"] for match in body["matches"]]
    assert scores == sorted(scores, reverse=True)


def test_candidate_matches_rank_every_job(client):
    body = client.get("/candidates/1/matches").json()

    assert len(body["matches"]) == 6
    assert body["matches"][0]["title"] == "Backend Detective"


def test_unknown_ids_return_404(client):
    assert client.get("/jobs/999/matches").status_code == 404
    assert client.get("/candidates/999/matches").status_code == 404


def test_limit_and_min_score_filter_ranked_matches(client):
    top_two = client.get("/jobs/1/matches?limit=2").json()["matches"]
    strong = client.get("/jobs/1/matches?min_score=90").json()["matches"]

    assert [match["name"] for match in top_two] == ["Sherlock H.", "Sheldon C."]
    assert [match["name"] for match in strong] == ["Sherlock H."]


def test_created_candidate_is_normalized_and_matched(client):
    response = client.post(
        "/candidates",
        json={
            "name": "Hercule P.",
            "skills": ["Deduction", "forensics", "deduction"],
            "experience_years": 30,
            "availability": "immediate",
            "traits": ["analytical", "autonomous"],
            "quirk": "Little grey cells.",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["skills"] == ["deduction", "forensics"]
    assert created["quirk"] == "Little grey cells."
    matches = client.get(f"/candidates/{created['id']}/matches").json()["matches"]
    assert matches[0]["title"] == "Backend Detective"

    duplicate = client.post(
        "/candidates",
        json={"name": "Hercule P.", "skills": ["x"], "experience_years": 1, "availability": "immediate"},
    )
    assert duplicate.status_code == 409


def test_created_job_ranks_existing_candidates(client):
    response = client.post(
        "/jobs",
        json={
            "title": "Chief Chemist",
            "required_skills": ["chemistry"],
            "min_experience": 5,
            "culture": ["reckless"],
            "tagline": "Mind the fumes.",
        },
    )

    assert response.status_code == 201
    assert response.json()["tagline"] == "Mind the fumes."
    matches = client.get(f"/jobs/{response.json()['id']}/matches").json()["matches"]
    assert matches[0]["name"] == "Rick S."
    assert client.post("/jobs", json={"title": "Chief Chemist", "required_skills": ["x"], "min_experience": 0}).status_code == 409
