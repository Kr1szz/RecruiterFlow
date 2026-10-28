from collections.abc import Iterable, Mapping
from typing import Any

# The two required criteria (skills, experience) carry 85 of the 100 points, so the
# soft signals can reorder close candidates but never outweigh a real skill gap.
SKILL_WEIGHT = 60.0
EXPERIENCE_WEIGHT = 25.0
CULTURE_WEIGHT = 10.0
AVAILABILITY_WEIGHT = 5.0

AVAILABILITY_FACTOR = {"immediate": 1.0, "2_weeks": 0.5, "not_looking": 0.0}
AVAILABILITY_LABEL = {
    "immediate": "available immediately",
    "2_weeks": "available in 2 weeks",
    "not_looking": "not currently looking",
}


def score_match(candidate: Mapping[str, Any], job: Mapping[str, Any]) -> dict[str, Any]:
    required = set(job["required_skills"])
    matched = sorted(required & set(candidate["skills"]))
    skill_ratio = len(matched) / len(required) if required else 1.0

    minimum = int(job["min_experience"])
    years = int(candidate["experience_years"])
    experience_ratio = 1.0 if minimum <= 0 else min(years / minimum, 1.0)

    culture = set(job.get("culture", []))
    shared_culture = sorted(culture & set(candidate.get("traits", [])))
    culture_ratio = len(shared_culture) / len(culture) if culture else 0.0

    availability = candidate.get("availability", "immediate")
    availability_ratio = AVAILABILITY_FACTOR.get(availability, 0.0)

    breakdown = {
        "skills": round(SKILL_WEIGHT * skill_ratio, 2),
        "experience": round(EXPERIENCE_WEIGHT * experience_ratio, 2),
        "culture": round(CULTURE_WEIGHT * culture_ratio, 2),
        "availability": round(AVAILABILITY_WEIGHT * availability_ratio, 2),
    }
    score = round(sum(breakdown.values()), 2)

    if matched:
        skill_reason = f"matches {len(matched)}/{len(required)} required skills ({', '.join(matched)})"
    else:
        skill_reason = f"matches 0/{len(required)} required skills"
    if years >= minimum:
        experience_reason = f"has {years} years of experience (minimum {minimum})"
    else:
        experience_reason = f"has {years} years of experience (minimum {minimum}; {minimum - years} short)"
    if shared_culture:
        culture_reason = f"shares culture traits ({', '.join(shared_culture)})"
    else:
        culture_reason = "no shared culture traits"
    availability_reason = AVAILABILITY_LABEL.get(availability, availability)
    reason = f"{skill_reason}; {experience_reason}; {culture_reason}; {availability_reason}."
    return {"score": score, "reason": reason, "matched_skills": matched, "breakdown": breakdown}


def _sort_key(item: dict[str, Any], label: str) -> tuple:
    return (-item["score"], -item["breakdown"]["skills"], item[label].casefold(), item["id"])


def ranked_candidates(candidates: Iterable[Mapping[str, Any]], job: Mapping[str, Any]) -> list[dict[str, Any]]:
    results = []
    for candidate in candidates:
        result = score_match(candidate, job)
        results.append({"id": candidate["id"], "name": candidate["name"], **result})
    return sorted(results, key=lambda item: _sort_key(item, "name"))


def ranked_jobs(candidate: Mapping[str, Any], jobs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for job in jobs:
        result = score_match(candidate, job)
        results.append({"id": job["id"], "title": job["title"], **result})
    return sorted(results, key=lambda item: _sort_key(item, "title"))
