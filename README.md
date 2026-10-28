# Recruiter Bot

FastAPI backend for ranking fictional candidates against jobs, plus the separate SQL Detective answers. The app uses PostgreSQL through Psycopg 3 and handwritten SQL only; there is no ORM or query builder.

## Setup and run

Requirements: Python 3.11+ and PostgreSQL 15+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/recruiter_bot'
createdb recruiter_bot
python -m app.seed
uvicorn app.main:app --reload
```

The seed command creates the app schema and inserts or updates exactly the 15 candidates and 6 jobs from the assignment. It can be rerun safely. OpenAPI docs are at `http://localhost:8000/docs`.

```bash
curl http://localhost:8000/jobs/1/matches
curl http://localhost:8000/candidates/1/matches
```

Run the tests with `pip install -r requirements-dev.txt && pytest`.

## Matching decisions

Every candidate/job pair receives a score from 0 to 100. Skill overlap contributes 70 points, proportional to the number of required skills the candidate has. Experience contributes 30 points: years divided by the minimum, capped at 1.0. Thus candidates who meet or exceed the minimum receive all experience points; candidates below it receive partial credit. A job with no required skills gets full skill points. The response explains the matched skill count and names, and compares years to the minimum.

Results include every candidate/job pair so a caller can see the full ranking, including weak matches. Ties are broken by case-insensitive name/title and then ID for repeatable output. Traits, culture keywords, availability, and quirks are preserved in the database but do not affect ranking; the brief makes those optional, and excluding them keeps scores explainable using the two required criteria.

## SQL Detective

`sql/hiring_ops_setup.sql` recreates the four tables and inserts the hiring-ops data exactly as supplied, including nullable values. Run it in an empty PostgreSQL database, then run `sql/sql_detective.sql`. Question 3 normalizes email case and surrounding whitespace to identify the two Ananya Rao records as one person; it counts distinct postings reached in the interview data. The bonus query uses `ROW_NUMBER()`, includes departments with zero successful placements, and breaks ties by recruiter ID.

## AI tools

I used ChatGPT to help inspect the assignment and draft the implementation. I reviewed the seed values, scoring rules, SQL interpretations, and tests against the brief and verified them locally.
