#!/usr/bin/env bash
# Start the Recruiter Bot API with one command.
#
#   ./scripts/run_backend.sh            # set up if needed, then start the API
#   ./scripts/run_backend.sh --reseed   # also rebuild the database from data/seed_data.json
#   ./scripts/run_backend.sh --reload   # restart the API automatically when code changes
#
# Steps: create .venv and install requirements; make sure PostgreSQL is reachable
# (starting the Docker database if it isn't); create the database if missing; seed
# it the first time; start uvicorn.
#
# Settings (environment variables):
#   DATABASE_URL  default postgresql://postgres:postgres@localhost:5432/recruiter_bot
#   HOST, PORT    where the API listens, default 127.0.0.1:8000
set -euo pipefail
cd "$(dirname "$0")/.."

RESEED=false
UVICORN_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --reseed) RESEED=true ;;
        --reload) UVICORN_ARGS+=(--reload) ;;
        -h | --help) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0 ;;
        *) echo "Unknown option: $arg (see --help)" >&2; exit 1 ;;
    esac
done

export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/recruiter_bot}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

step() { printf '\n==> %s\n' "$*"; }
fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }

# 1. Python environment
step "Python environment"
command -v python3 >/dev/null || fail "python3 is not installed"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' || fail "Python 3.11+ is required"
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
    echo "Created .venv"
fi
.venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt
echo "Requirements installed"

# 2. Database. db_status prints one of: ready, missing_db, unreachable, error:<message>.
# A missing database is created on the same server.
db_status() {
    .venv/bin/python - <<'EOF'
import psycopg
from app.db import database_url

url = database_url()
try:
    psycopg.connect(url, connect_timeout=3).close()
    print("ready")
except psycopg.OperationalError as exc:
    message = str(exc)
    if "does not exist" in message and "database" in message:
        print("missing_db")
    elif any(text in message for text in ("Connection refused", "No such file", "timeout", "closed the connection")):
        print("unreachable")
    else:
        print("error:" + message.strip().splitlines()[0])
EOF
}

create_database() {
    .venv/bin/python - <<'EOF'
import psycopg
from psycopg import conninfo
from app.db import database_url

params = conninfo.conninfo_to_dict(database_url())
name = params["dbname"]
with psycopg.connect(conninfo.make_conninfo(database_url(), dbname="postgres"), autocommit=True) as connection:
    connection.execute(f'CREATE DATABASE "{name}"')
print(f"Created database {name}")
EOF
}

step "PostgreSQL"
status="$(db_status)"
if [ "$status" = unreachable ]; then
    command -v docker >/dev/null || fail "PostgreSQL is not reachable at DATABASE_URL and Docker is not installed"
    # Publish the container on the port DATABASE_URL points at.
    POSTGRES_PORT="$(.venv/bin/python -c 'from psycopg import conninfo; from app.db import database_url; print(conninfo.conninfo_to_dict(database_url()).get("port") or 5432)')"
    export POSTGRES_PORT
    echo "Not reachable; starting PostgreSQL in Docker on port $POSTGRES_PORT"
    docker compose up -d --wait
    # The container reports healthy while first-time initialisation is still
    # finishing, so keep retrying for a short while.
    for _ in $(seq 30); do
        status="$(db_status)"
        [ "$status" != unreachable ] && break
        sleep 1
    done
fi
if [ "$status" = missing_db ]; then
    create_database
    status="$(db_status)"
fi
case "$status" in
    ready) echo "Connected" ;;
    error:*) fail "${status#error:}" ;;
    *) fail "could not connect to PostgreSQL ($status)" ;;
esac

# 3. Seed on first run (or when asked). job_culture only exists in the current schema,
# so an older schema also triggers a rebuild.
seeded="$(.venv/bin/python -c '
from app.db import get_connection
with get_connection() as c:
    print(c.execute("SELECT to_regclass(%s) IS NOT NULL AS ok", ("public.job_culture",)).fetchone()["ok"])
')"
if $RESEED || [ "$seeded" != True ]; then
    step "Seeding database"
    .venv/bin/python -m app.seed
else
    echo "Database already seeded (use --reseed to rebuild it)"
fi

# 4. API
step "Starting API on http://$HOST:$PORT  (docs: http://$HOST:$PORT/docs, stop with Ctrl+C)"
exec .venv/bin/uvicorn app.main:app --host "$HOST" --port "$PORT" ${UVICORN_ARGS[@]+"${UVICORN_ARGS[@]}"}
