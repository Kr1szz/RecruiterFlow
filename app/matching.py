from collections.abc import Iterable, Mapping
from typing import Any


SKILL_WEIGHT = 70.0
EXPERIENCE_WEIGHT = 30.0


def score_match(candidate: Mapping[str, Any], job: Mapping[str, Any]) -> dict[str, Any]:
    required = set(job["required_skills"])
    candidate_skills = set(candidate["skills"])
    matched = sorted(required & candidate_skills)
    skill_ratio = len(matched) / len(required) if required else 1.0

    minimum = int(job["min_experience"])
    years = int(candidate["experience_years"])
    experience_ratio = 1.0 if minimum <= 0 else min(years / minimum, 1.0)
    score = round(SKILL_WEIGHT * skill_ratio + EXPERIENCE_WEIGHT * experience_ratio, 2)

    if matched:
        skill_reason = f"matches {len(matched)}/{len(required)} required skills ({', '.join(matched)})"
    else:
        skill_reason = f"matches 0/{len(required)} required skills"
    if years >= minimum:
        experience_reason = f"has {years} years of experience (minimum {minimum})"
    else:
        experience_reason = f"has {years} years of experience (minimum {minimum}; {minimum - years} short)"
    return {"score": score, "reason": f"{skill_reason}; {experience_reason}.", "matched_skills": matched}


def ranked_candidates(candidates: Iterable[Mapping[str, Any]], job: Mapping[str, Any]) -> list[dict[str, Any]]:
    results = []
    for candidate in candidates:
        result = score_match(candidate, job)
        results.append({"id": candidate["id"], "name": candidate["name"], **result})
    return sorted(results, key=lambda item: (-item["score"], item["name"].casefold(), item["id"]))


def ranked_jobs(candidate: Mapping[str, Any], jobs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for job in jobs:
        result = score_match(candidate, job)
        results.append({"id": job["id"], "title": job["title"], **result})
    return sorted(results, key=lambda item: (-item["score"], item["title"].casefold(), item["id"]))

