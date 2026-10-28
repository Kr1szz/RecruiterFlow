from app.matching import ranked_candidates, ranked_jobs, score_match


def test_score_combines_skill_overlap_and_capped_experience():
    candidate = {"id": 1, "name": "Sherlock H.", "skills": ["deduction", "forensics"], "experience_years": 8}
    job = {"id": 1, "title": "Backend Detective", "required_skills": ["deduction", "pattern-recognition", "forensics"], "min_experience": 3}

    result = score_match(candidate, job)

    assert result["score"] == 76.67
    assert result["matched_skills"] == ["deduction", "forensics"]
    assert "2/3 required skills" in result["reason"]
    assert "8 years of experience (minimum 3)" in result["reason"]


def test_experience_below_requirement_is_scaled_and_explained():
    candidate = {"id": 1, "name": "A", "skills": ["x"], "experience_years": 1}
    job = {"id": 1, "title": "J", "required_skills": ["x"], "min_experience": 4}

    result = score_match(candidate, job)

    assert result["score"] == 77.5
    assert "3 short" in result["reason"]


def test_ranking_is_deterministic_and_reverse_direction_works():
    candidate = {"id": 2, "name": "B", "skills": ["x"], "experience_years": 5}
    jobs = [
        {"id": 2, "title": "Z job", "required_skills": ["x"], "min_experience": 2},
        {"id": 1, "title": "A job", "required_skills": ["x"], "min_experience": 2},
    ]

    assert [item["id"] for item in ranked_jobs(candidate, jobs)] == [1, 2]
    candidates = [
        {"id": 2, "name": "Z", "skills": ["x"], "experience_years": 5},
        {"id": 1, "name": "A", "skills": ["x"], "experience_years": 5},
    ]
    assert [item["id"] for item in ranked_candidates(candidates, jobs[0])] == [1, 2]
