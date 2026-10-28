#!/usr/bin/env bash
# Run the SQL Detective answers with one command.
#
# Loads the hiring-ops dataset into a throwaway schema inside a transaction, runs
# sql/sql_detective.sql, then rolls back, so nothing is left in the database.
#
#   ./scripts/sql_detective.sh                    # uses DATABASE_URL (or the default below)
#   PSQL="docker compose exec -T db psql -U postgres -d recruiter_bot" ./scripts/sql_detective.sh
set -euo pipefail
cd "$(dirname "$0")/.."

DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/recruiter_bot}"
PSQL="${PSQL:-psql $DATABASE_URL}"

{
    echo "BEGIN;"
    echo "CREATE SCHEMA sql_detective;"
    echo "SET LOCAL search_path TO sql_detective;"
    cat sql/hiring_ops_setup.sql
    echo "\\set ECHO queries"
    # Print each "-- Question N: ..." comment as a heading above its result.
    sed -E 's/^-- (Question [0-9].*)$/\\echo == \1/' sql/sql_detective.sql
    echo "\\set ECHO none"
    echo "ROLLBACK;"
} | $PSQL -X -q -v ON_ERROR_STOP=1
