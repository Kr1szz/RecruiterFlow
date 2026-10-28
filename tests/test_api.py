import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import get_repository

SHERLOCK = {
    "id": 1,
    "name": "Sherlock H.",
    "experience_years": 8,
    "skills": ["deduction", "forensics"],
    "traits": ["analytical"],
    "availability": "immediate",
}
DETECTIVE = {
    "id": 1,
    "title": "Backend Detective",
    "min_experience": 3,
    "required_skills": ["deduction", "forensics"],
    "culture": ["analytical"],
}


class FakeRepository:
    def get_job(self, job_id):
        return DETECTIVE if job_id == 1 else None

    def get_candidate(self, candidate_id):
        return SHERLOCK if candidate_id == 1 else None

    def list_candidates(self):
        return [SHERLOCK]

    def list_jobs(self):
        return [DETECTIVE]


@pytest.fixture
def client():
    app.dependency_overrides[get_repository] = FakeRepository
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_job_matches_returns_ranked_explanation(client):
    body = client.get("/jobs/1/matches").json()

    assert body["subject_id"] == 1
    match = body["matches"][0]
    assert match["name"] == "Sherlock H."
    assert "title" not in match
    assert match["score"] == 100.0
    assert match["breakdown"] == {"skills": 60.0, "experience": 25.0, "culture": 10.0, "availability": 5.0}
    assert "2/2 required skills" in match["reason"]


def test_get_candidate_matches_returns_jobs(client):
    body = client.get("/candidates/1/matches").json()

    assert body["subject_id"] == 1
    assert body["matches"][0]["title"] == "Backend Detective"
    assert "name" not in body["matches"][0]


def test_unknown_subject_returns_404(client):
    assert client.get("/jobs/999/matches").status_code == 404
    assert client.get("/candidates/999/matches").status_code == 404


def test_matching_get_routes_are_registered_in_openapi():
    paths = app.openapi()["paths"]

    assert "get" in paths["/jobs/{job_id}/matches"]
    assert "get" in paths["/candidates/{candidate_id}/matches"]


def test_limit_and_min_score_must_be_in_range(client):
    assert client.get("/jobs/1/matches?limit=0").status_code == 422
    assert client.get("/jobs/1/matches?min_score=101").status_code == 422


def test_create_candidate_rejects_invalid_body(client):
    response = client.post(
        "/candidates",
        json={"name": "Nobody", "skills": [" "], "experience_years": -1, "availability": "someday"},
    )

    assert response.status_code == 422
    invalid_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert {"experience_years", "availability"} <= invalid_fields
    assert any("skills" in error["loc"] for error in response.json()["detail"])
