# Recruiter Bot

FastAPI backend for ranking fictional candidates against jobs, plus the separate SQL Detective answers. The app uses PostgreSQL through Psycopg 3 and handwritten SQL only; there is no ORM or query builder.

For a walkthrough of the data model, request flows and scoring, see [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md).

## Setup and run

Requirements: Python 3.11+ and either Docker or PostgreSQL 15+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Option A: Postgres in Docker (creates the recruiter_bot database for you)
docker compose up -d --wait
# Option B: an existing local Postgres
createdb recruiter_bot

export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/recruiter_bot'
python -m app.seed
uvicorn app.main:app --reload
```

If port 5432 is already in use, start Docker with `POSTGRES_PORT=5433 docker compose up -d --wait` and use `localhost:5433` in `DATABASE_URL`. Stop it with `docker compose down -v`.

The seed command rebuilds the app schema from `sql/schema.sql` and, using the same repository code as the POST endpoints, loads the 15 candidates and 6 jobs from `data/seed_data.json`. It drops and recreates the tables, so it can be rerun safely and IDs always come out the same (candidates 1–15 and jobs 1–6, in file order). OpenAPI docs are at `http://localhost:8000/docs`.

```bash
# Ranked matches (both directions); limit and min_score are optional
curl http://localhost:8000/jobs/1/matches
curl 'http://localhost:8000/candidates/1/matches?limit=3&min_score=50'

# Add a candidate or a job (skills/traits are lowercased and de-duplicated)
curl -X POST http://localhost:8000/candidates -H 'Content-Type: application/json' \
  -d '{"name": "Hercule P.", "skills": ["deduction", "forensics"], "experience_years": 30,
       "availability": "immediate", "traits": ["analytical"], "quirk": "Little grey cells."}'
curl -X POST http://localhost:8000/jobs -H 'Content-Type: application/json' \
  -d '{"title": "Chief Chemist", "required_skills": ["chemistry"], "min_experience": 5, "culture": ["reckless"]}'
```

| Endpoint | Notes |
|---|---|
| `GET /jobs/{id}/matches` | Every candidate ranked for the job. 404 for an unknown job. |
| `GET /candidates/{id}/matches` | Every job ranked for the candidate. 404 for an unknown candidate. |
| `POST /candidates`, `POST /jobs` | 201 with the stored record, 409 if the name/title exists, 422 for invalid input. |

Each match has `score` (0–100), a `reason` sentence and a per-signal `breakdown`.

Run the tests with `pip install -r requirements-dev.txt && pytest`. `tests/test_integration.py` seeds the database at `DATABASE_URL` and calls the real endpoints; it is skipped if PostgreSQL is not reachable. **It rebuilds that database**, so point it at a scratch DB if you care about its contents.

## Schema

`candidates` and `jobs` hold the scalar fields. Skills and traits each live in a lookup table (`skills`, `traits`) and are linked through join tables (`candidate_skills`, `job_skills`, `candidate_traits`, `job_culture`). Candidate traits and job culture keywords share the one `traits` vocabulary, so "does this candidate fit the culture?" is a join on `trait_id` rather than string matching. `availability` is constrained to `immediate`, `2_weeks` or `not_looking`. Matches are not stored: with 15 × 6 pairs it is cheaper and always up to date to score them on request.

All SQL is handwritten (`sql/schema.sql`, `app/repository.py`, `app/seed.py`); Psycopg is used only as the driver.

## Matching decisions

Every candidate/job pair receives a score from 0 to 100, made up of four parts:

| Signal | Points | Rule |
|---|---|---|
| Skill overlap | 60 | share of the job's required skills the candidate has |
| Experience | 25 | years ÷ minimum, capped at 1.0, so partial credit when below the minimum |
| Culture fit | 10 | share of the job's culture keywords found in the candidate's traits |
| Availability | 5 | immediate 1.0, 2 weeks 0.5, not looking 0 |

The two required criteria carry 85 of the 100 points, so culture and availability can reorder close candidates but cannot hide a real skill gap. For example, Olivia P. (all three Incident Commander skills, 2 weeks away) still beats Katniss E. (two skills, available now). Skills outweigh experience because the experience bar is a minimum, and being far above it does not make someone a better fit; it is capped for the same reason.

Candidates who are not looking are **ranked lower, not removed**. A recruiter may still want to approach Tony S. or Miranda P., and hiding them would hide that choice. Each response has a `reason` sentence and a `breakdown` of points per signal, so any score can be traced.

Results include every pair, weak matches included. Ties are broken by skill points (the stronger skill match wins), then case-insensitive name/title, then ID, so output is repeatable. One visible effect: Dwight S. and Michael S. tie at 70 for Sales Engineer. Michael's culture point is cancelled out by not looking, and Dwight wins on the name tie-break. Quirks are stored but not scored, since they are flavour text rather than structured signals.

## SQL Detective

`sql/hiring_ops_setup.sql` recreates the four tables and inserts the hiring-ops data exactly as supplied, including nullable values. Run it in an empty PostgreSQL database, then run `sql/sql_detective.sql`. Question 3 normalizes email case and surrounding whitespace to identify the two Ananya Rao records as one person; it counts distinct postings reached in the interview data. Because `applicants` has no posting column, "applied to a posting" is inferred from `interviews`. Question 4 rounds the conversion rate to two decimals. The bonus query uses `ROW_NUMBER()`, so it returns exactly one recruiter per department; it includes departments with zero successful placements and breaks ties by recruiter ID.

## What I would do next

- `PUT`/`DELETE` for candidates and jobs, and pagination for listing them.
- Skill synonyms or groupings (e.g. `crisis-management` ≈ `incident-response`) instead of exact names only.
- Precompute and store scores in a `matches` table if the data grows beyond what is cheap to score per request.

## AI tools

I used ChatGPT to help inspect the assignment and draft the implementation. I reviewed the seed values, scoring rules, SQL interpretations, and tests against the brief and verified them locally.
