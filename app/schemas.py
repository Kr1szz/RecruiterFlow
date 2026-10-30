from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScoreBreakdown(BaseModel):
    skills: float = Field(ge=0)
    experience: float = Field(ge=0)
    culture: float = Field(ge=0)
    availability: float = Field(ge=0)


class JobCandidateMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    score: float = Field(ge=0, le=100)
    reason: str
    breakdown: ScoreBreakdown


class JobMatchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    score: float = Field(ge=0, le=100)
    reason: str
    breakdown: ScoreBreakdown


class JobMatchesResponse(BaseModel):
    subject_id: int
    matches: list[JobCandidateMatch]


class CandidateMatchesResponse(BaseModel):
    subject_id: int
    matches: list[JobMatchItem]


def _normalize_names(values: list[str]) -> list[str]:
    """Lowercase, trim and de-duplicate skill/trait names, keeping first-seen order."""
    cleaned = [value.strip().lower() for value in values]
    if any(not value for value in cleaned):
        raise ValueError("names must not be blank")
    return list(dict.fromkeys(cleaned))


class CandidateIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    skills: list[str] = Field(min_length=1)
    experience_years: int = Field(ge=0, le=80)
    availability: Literal["immediate", "2_weeks", "not_looking"]
    traits: list[str] = []
    quirk: str = ""

    _clean_names = field_validator("skills", "traits")(_normalize_names)


class JobIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100)
    required_skills: list[str] = Field(min_length=1)
    min_experience: int = Field(ge=0, le=80)
    culture: list[str] = []
    tagline: str = ""

    _clean_names = field_validator("required_skills", "culture")(_normalize_names)


class CandidateOut(BaseModel):
    id: int
    name: str
    experience_years: int
    availability: str
    skills: list[str]
    traits: list[str]
    quirk: str


class JobOut(BaseModel):
    id: int
    title: str
    min_experience: int
    required_skills: list[str]
    culture: list[str]
    tagline: str
