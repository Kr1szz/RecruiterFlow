# Recruiter Bot

FastAPI backend that ranks fictional candidates against jobs, plus the separate SQL Detective answers. It uses PostgreSQL through Psycopg 3 with handwritten SQL only; there is no ORM or query builder.

For a walkthrough of the data model, request flows and scoring, see [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md).

## Setup and run

Requirements: Python 3.11+ and either Docker or PostgreSQL 15+.

### Quick start

```bash
./scripts/run_backend.sh            # add --reseed to rebuild the data, --reload while developing
```

This creates `.venv` and installs the requirements. If nothing is reachable at `DATABASE_URL`, it starts PostgreSQL in Docker; if the database doesn't exist, it creates it. It seeds on the first run only, then starts the API on `http://127.0.0.1:8000`. Run `./scripts/run_backend.sh --help` for options.

### Step by step

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

The seed command rebuilds the app schema from `sql/schema.sql` and loads the 15 candidates and 6 jobs from `data/seed_data.json`, using the same repository code as the POST endpoints. Because it drops and recreates the tables, it can be rerun safely, and IDs always come out the same: candidates 1–15 and jobs 1–6, in file order.

## Using the API

Interactive OpenAPI docs are at `http://localhost:8000/docs`.

| Endpoint | Notes |
|---|---|
| `GET /jobs/{id}/matches` | Every candidate ranked for the job. 404 for an unknown job. |
| `GET /candidates/{id}/matches` | Every job ranked for the candidate. 404 for an unknown candidate. |
| `POST /candidates`, `POST /jobs` | 201 with the stored record, 409 if the name/title exists, 422 for invalid input. |

Both match endpoints accept optional `limit` (keep the first N) and `min_score` (drop lower scores). Each match has a `score` (0–100), a `reason` sentence, and a `breakdown` of points per signal.

### curl

```bash
# Ranked matches, both directions
curl http://localhost:8000/jobs/1/matches
curl 'http://localhost:8000/candidates/1/matches?limit=3&min_score=50'

# Add a candidate or a job (skills/traits are lowercased and de-duplicated)
curl -X POST http://localhost:8000/candidates -H 'Content-Type: application/json' \
  -d '{"name": "Hercule P.", "skills": ["deduction", "forensics"], "experience_years": 30,
       "availability": "immediate", "traits": ["analytical"], "quirk": "Little grey cells."}'
curl -X POST http://localhost:8000/jobs -H 'Content-Type: application/json' \
  -d '{"title": "Chief Chemist", "required_skills": ["chemistry"], "min_experience": 5, "culture": ["reckless"]}'
```

### Postman

[postman/RecruiterBot.postman_collection.json](postman/RecruiterBot.postman_collection.json) covers every endpoint, grouped into *Matching*, *Ingestion* and *Errors*, with test assertions on each request.

1. Start the API with `./scripts/run_backend.sh`.
2. In Postman, choose **Import** and select the collection file.
3. Open any request and click **Send**. The response is in **Body**, and the checks are in **Test Results**.
4. To run everything, open the collection's **⋯** menu → **Run collection** → **Run Recruiter Bot**. Expect 12 requests and 31 passing tests.

Some notes on running it:
- **Run the collection in order.** *Duplicate candidate (409)* reuses the name created by *Create a candidate*.
- **Different server address?** If the API isn't on `http://localhost:8000`, change the collection's `baseUrl` variable.
- **Re-running is fine.** The create requests add a timestamp to each name, so you can run the collection again without reseeding.
- **Postman in the browser** needs the Postman Desktop Agent to reach `localhost`.

The same collection also runs from the command line:

```bash
npx newman run postman/RecruiterBot.postman_collection.json
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

| File | What it checks | Database |
|---|---|---|
| `tests/test_matching.py` | Scoring, reasons, tie-breaking | Not needed |
| `tests/test_api.py` | Routes, status codes, validation (fake repository) | Not needed |
| `tests/test_integration.py` | Schema, seed, real SQL and endpoints end to end | Uses `DATABASE_URL`; skipped if unreachable |

**The integration tests rebuild the database at `DATABASE_URL`**, so point them at a scratch database if you care about its contents.

## Schema

`candidates` and `jobs` hold the scalar fields. Skills and traits each live in a lookup table (`skills`, `traits`) and are linked through join tables (`candidate_skills`, `job_skills`, `candidate_traits`, `job_culture`).

Candidate traits and job culture keywords share the one `traits` vocabulary. That makes "does this candidate fit the culture?" a join on `trait_id` rather than string matching.

`availability` is constrained to `immediate`, `2_weeks` or `not_looking`.

Matches are not stored. With 15 × 6 pairs it is cheaper, and always up to date, to score them on request.

All SQL is handwritten (`sql/schema.sql`, `app/repository.py`, `app/seed.py`); Psycopg is used only as the driver.

## Matching decisions

Every candidate/job pair receives a score from 0 to 100, made up of four parts:

| Signal | Points | Rule |
|---|---|---|
| Skill overlap | 60 | share of the job's required skills the candidate has |
| Experience | 25 | years ÷ minimum, capped at 1.0, so partial credit when below the minimum |
| Culture fit | 10 | share of the job's culture keywords found in the candidate's traits |
| Availability | 5 | immediate 1.0, 2 weeks 0.5, not looking 0 |

**The two required criteria dominate.** Skills and experience carry 85 of the 100 points, so culture and availability can reorder close candidates but cannot hide a real skill gap. For example, Olivia P. has all three Incident Commander skills but is two weeks away; she still beats Katniss E., who has two of the skills and is available now.

**Skills outweigh experience.** The experience bar is a minimum, and being far above it doesn't make someone a better fit. That is also why experience is capped.

**Candidates who are not looking are ranked lower, not removed.** A recruiter may still want to approach Tony S. or Miranda P., and hiding them would take that choice away. Each response has a `reason` sentence and a `breakdown` of points per signal, so any score can be traced.

**Every pair is returned**, weak matches included.

**Ties are broken by** skill points (the stronger skill match wins), then name or title (ignoring case), then ID, so the output is repeatable. One visible effect: Dwight S. and Michael S. tie at 70 for Sales Engineer. Michael's culture point is cancelled out by his not-looking status, and Dwight wins on the name tie-break.

**Quirks are stored but not scored**, since they are flavour text rather than structured signals.

## SQL Detective

Run every answer with one command. It needs `psql` and uses `DATABASE_URL`, or the default above:

```bash
./scripts/sql_detective.sh
# or against the Docker database:
PSQL="docker compose exec -T db psql -U postgres -d recruiter_bot" ./scripts/sql_detective.sh
```

The script loads the dataset into a temporary schema inside a transaction, prints each query with its result, and rolls back. It leaves nothing behind, so it can be run any number of times.

To run it by hand instead, load `sql/hiring_ops_setup.sql` into an empty database, then run `sql/sql_detective.sql`. The setup file creates the four tables and inserts the hiring-ops data exactly as supplied, nullable values included.

Notes on the answers:
- **Question 3** normalizes email case and surrounding whitespace, so the two Ananya Rao records count as one person.
- **Where applications come from:** the `applicants` table has no posting column, so "applied to a posting" is inferred from `interviews`.
- **Question 4** rounds the conversion rate to two decimals.
- **The bonus query** uses `ROW_NUMBER()`, so it returns exactly one recruiter per department. It includes departments with zero successful placements and breaks ties by recruiter ID.

## What I would do next

- `PUT`/`DELETE` for candidates and jobs, and pagination for listing them.
- Skill synonyms or groupings (e.g. `crisis-management` ≈ `incident-response`) instead of exact names only.
- Precompute and store scores in a `matches` table if the data grows beyond what is cheap to score per request.

## AI tools

I used two AI tools, at different stages.

**ChatGPT (first draft).** I used it to read through the assignment and draft the initial implementation: the FastAPI skeleton, the first schema, the seed script, and the SQL Detective queries.

**Claude Code (review, fixes and extensions).** I then used Claude Code in my editor to review the project against the brief and finish it:

- **Finding a real bug.** It found that I had rewritten `sql/schema.sql` into the normalized design but never updated `app/seed.py` or `app/repository.py`. A fresh seed would have failed; the API only worked because my local database still had the old tables. My unit tests used fakes, so none of them caught it.
- **Decisions I made.** It asked before choosing a direction. I chose to keep the normalized schema rather than revert, and to add culture and availability as small, secondary signals. It proposed the specific weights (60/25/10/5), the tie-break order, and ranking "not looking" candidates lower instead of hiding them. Before accepting them, I checked the resulting rankings by hand against the seed data, for example Sherlock first for Backend Detective and Olivia ahead of Katniss for Incident Commander.
- **Code it wrote.**
  - The schema and seed changes, the rewritten repository queries, and the updated matching algorithm.
  - The POST endpoints and the `limit`/`min_score` filters.
  - `docker-compose.yml`, `scripts/run_backend.sh` and `scripts/sql_detective.sh`.
  - The Postman collection and `docs/HOW_IT_WORKS.md`.
- **Tests and checks.**
  - **Integration tests:** it added tests that run against a real PostgreSQL database, the kind of test that would have caught the schema bug.
  - **Clean install:** it ran one in a separate folder, which showed that `httpx` was missing from `requirements-dev.txt`.
  - **Startup race:** testing `run_backend.sh` against a fresh Docker database exposed one, and it fixed it.
  - **SQL Detective:** it ran the original answers against the dataset to confirm them, then made only small fixes (rounding, and correcting comments).

All the SQL is still handwritten, and nothing goes through an ORM or query builder. I have read through every file and can explain how each part works and why it was built that way.
