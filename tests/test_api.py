from fastapi import HTTPException

from app.main import app
from app.routes import matches_for_candidate, matches_for_job


class FakeRepository:
    def get_job(self, job_id):
        return {"id": 1, "title": "Backend Detective", "min_experience": 3, "required_skills": ["deduction", "forensics"]} if job_id == 1 else None

    def get_candidate(self, candidate_id):
        return {"id": 1, "name": "Sherlock H.", "experience_years": 8, "skills": ["deduction", "forensics"]} if candidate_id == 1 else None

    def list_candidates(self):
        return [{"id": 1, "name": "Sherlock H.", "experience_years": 8, "skills": ["deduction", "forensics"]}]

    def list_jobs(self):
        return [{"id": 1, "title": "Backend Detective", "min_experience": 3, "required_skills": ["deduction", "forensics"]}]


def fake_repository():
    return FakeRepository()


def test_get_job_matches_returns_ranked_explanation():
    response = matches_for_job(1, FakeRepository())

    assert response.subject_id == 1
    assert response.matches[0].name == "Sherlock H."
    assert not hasattr(response.matches[0], "title")
    assert response.matches[0].score == 100.0
    assert "2/2 required skills" in response.matches[0].reason


def test_get_candidate_matches_returns_jobs():
    response = matches_for_candidate(1, FakeRepository())

    assert response.subject_id == 1
    assert response.matches[0].title == "Backend Detective"
    assert not hasattr(response.matches[0], "name")


def test_matching_get_routes_are_registered_in_openapi():
    paths = app.openapi()["paths"]

    assert "/jobs/{job_id}/matches" in paths
    assert "get" in paths["/jobs/{job_id}/matches"]
    assert "/candidates/{candidate_id}/matches" in paths
    assert "get" in paths["/candidates/{candidate_id}/matches"]
    schemas = app.openapi()["components"]["schemas"]
    assert "name" in schemas["JobCandidateMatch"]["properties"]
    assert "title" not in schemas["JobCandidateMatch"]["properties"]
    assert "title" in schemas["JobMatchItem"]["properties"]
    assert "name" not in schemas["JobMatchItem"]["properties"]


def test_unknown_subject_raises_http_404():
    try:
        matches_for_job(999, FakeRepository())
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("Expected a 404 for an unknown job")

    try:
        matches_for_candidate(999, FakeRepository())
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("Expected a 404 for an unknown candidate")
