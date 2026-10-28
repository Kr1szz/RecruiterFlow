from collections.abc import Iterator
from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import get_connection
from app.matching import ranked_candidates, ranked_jobs
from app.repository import RecruiterRepository
from app.schemas import (
    CandidateIn,
    CandidateMatchesResponse,
    CandidateOut,
    JobIn,
    JobMatchesResponse,
    JobOut,
)

router = APIRouter()

Limit = Annotated[int | None, Query(ge=1, description="Return at most this many matches")]
MinScore = Annotated[float, Query(ge=0, le=100, description="Drop matches scoring below this")]


def get_repository() -> Iterator[RecruiterRepository]:
    with get_connection() as connection:
        yield RecruiterRepository(connection)


def filter_matches(matches: list[dict], limit: int | None, min_score: float) -> list[dict]:
    kept = [match for match in matches if match["score"] >= min_score]
    return kept[:limit] if limit is not None else kept


@router.get("/jobs/{job_id}/matches", response_model=JobMatchesResponse)
def matches_for_job(
    job_id: int,
    repository: RecruiterRepository = Depends(get_repository),
    limit: Limit = None,
    min_score: MinScore = 0,
) -> JobMatchesResponse:
    job = repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    matches = ranked_candidates(repository.list_candidates(), job)
    return JobMatchesResponse(subject_id=job_id, matches=filter_matches(matches, limit, min_score))


@router.get("/candidates/{candidate_id}/matches", response_model=CandidateMatchesResponse)
def matches_for_candidate(
    candidate_id: int,
    repository: RecruiterRepository = Depends(get_repository),
    limit: Limit = None,
    min_score: MinScore = 0,
) -> CandidateMatchesResponse:
    candidate = repository.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    matches = ranked_jobs(candidate, repository.list_jobs())
    return CandidateMatchesResponse(subject_id=candidate_id, matches=filter_matches(matches, limit, min_score))


@router.post("/candidates", response_model=CandidateOut, status_code=status.HTTP_201_CREATED)
def create_candidate(
    body: CandidateIn, repository: RecruiterRepository = Depends(get_repository)
) -> CandidateOut:
    try:
        candidate_id = repository.create_candidate(**body.model_dump())
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail=f"Candidate {body.name!r} already exists") from None
    return CandidateOut(**repository.get_candidate(candidate_id))


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(body: JobIn, repository: RecruiterRepository = Depends(get_repository)) -> JobOut:
    try:
        job_id = repository.create_job(**body.model_dump())
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail=f"Job {body.title!r} already exists") from None
    return JobOut(**repository.get_job(job_id))
