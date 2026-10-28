from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException

from app.db import get_connection
from app.matching import ranked_candidates, ranked_jobs
from app.repository import RecruiterRepository
from app.schemas import CandidateMatchesResponse, JobMatchesResponse

router = APIRouter()


def get_repository() -> Iterator[RecruiterRepository]:
    with get_connection() as connection:
        yield RecruiterRepository(connection)


@router.get("/jobs/{job_id}/matches", response_model=JobMatchesResponse)
def matches_for_job(job_id: int, repository: RecruiterRepository = Depends(get_repository)) -> JobMatchesResponse:
    job = repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    matches = ranked_candidates(repository.list_candidates(), job)
    return JobMatchesResponse(subject_id=job_id, matches=matches)


@router.get("/candidates/{candidate_id}/matches", response_model=CandidateMatchesResponse)
def matches_for_candidate(
    candidate_id: int, repository: RecruiterRepository = Depends(get_repository)
) -> CandidateMatchesResponse:
    candidate = repository.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    matches = ranked_jobs(candidate, repository.list_jobs())
    return CandidateMatchesResponse(subject_id=candidate_id, matches=matches)

