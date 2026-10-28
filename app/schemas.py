from pydantic import BaseModel, ConfigDict, Field


class JobCandidateMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    score: float = Field(ge=0, le=100)
    reason: str


class JobMatchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    score: float = Field(ge=0, le=100)
    reason: str


class JobMatchesResponse(BaseModel):
    subject_id: int
    matches: list[JobCandidateMatch]


class CandidateMatchesResponse(BaseModel):
    subject_id: int
    matches: list[JobMatchItem]

