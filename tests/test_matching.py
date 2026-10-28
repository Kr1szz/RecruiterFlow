from app.matching import ranked_candidates, ranked_jobs, score_match


def make_candidate(**overrides):
    candidate = {"id": 1, "name": "A", "skills": ["x"], "experience_years": 5, "traits": [], "availability": "immediate"}
    return {**candidate, **overrides}


def make_job(**overrides):
    job = {"id": 1, "title": "J", "required_skills": ["x"], "min_experience": 2, "culture": []}
    return {**job, **overrides}


def test_score_combines_all_signals():
    candidate = make_candidate(
        name="Sherlock H.", skills=["deduction", "forensics"], experience_years=8, traits=["analytical", "blunt"]
    )
    job = make_job(
        title="Backend Detective",
        required_skills=["deduction", "pattern-recognition", "forensics"],
        min_experience=3,
        culture=["analytical", "autonomous"],
    )

    result = score_match(candidate, job)

    assert result["breakdown"] == {"skills": 40.0, "experience": 25.0, "culture": 5.0, "availability": 5.0}
    assert result["score"] == 75.0
    assert result["matched_skills"] == ["deduction", "forensics"]
    assert "2/3 required skills" in result["reason"]
    assert "8 years of experience (minimum 3)" in result["reason"]
    assert "shares culture traits (analytical)" in result["reason"]
    assert "available immediately" in result["reason"]


def test_experience_below_requirement_is_scaled_and_explained():
    result = score_match(make_candidate(experience_years=1), make_job(min_experience=4))

    assert result["breakdown"]["experience"] == 6.25
    assert "3 short" in result["reason"]


def test_availability_lowers_score_without_excluding():
    scores = {
        availability: score_match(make_candidate(availability=availability), make_job())["breakdown"]["availability"]
        for availability in ("immediate", "2_weeks", "not_looking")
    }

    assert scores == {"immediate": 5.0, "2_weeks": 2.5, "not_looking": 0.0}


def test_job_without_culture_keywords_gives_no_culture_points():
    result = score_match(make_candidate(traits=["calm"]), make_job(culture=[]))

    assert result["breakdown"]["culture"] == 0.0
    assert "no shared culture traits" in result["reason"]


def test_ties_prefer_stronger_skill_match_before_name():
    job = make_job(required_skills=["x", "y"], min_experience=2, culture=["calm", "kind"])
    # Same total (65): Z = 60 skills + 5 availability; A = 30 skills + 25 experience + 10 culture.
    skilled = make_candidate(id=1, name="Z", skills=["x", "y"], experience_years=0)
    culture_fit = make_candidate(
        id=2, name="A", skills=["x"], experience_years=2, traits=["calm", "kind"], availability="not_looking"
    )
    assert score_match(skilled, job)["score"] == score_match(culture_fit, job)["score"]

    assert [item["name"] for item in ranked_candidates([culture_fit, skilled], job)] == ["Z", "A"]


def test_ranking_is_deterministic_and_reverse_direction_works():
    candidate = make_candidate(id=2, name="B")
    jobs = [make_job(id=2, title="Z job"), make_job(id=1, title="A job")]

    assert [item["id"] for item in ranked_jobs(candidate, jobs)] == [1, 2]
    candidates = [make_candidate(id=2, name="Z"), make_candidate(id=1, name="A")]
    assert [item["id"] for item in ranked_candidates(candidates, jobs[0])] == [1, 2]
