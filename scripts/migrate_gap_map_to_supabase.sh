#!/bin/bash
# Migrate gap_map_entries from local PostgreSQL to Supabase.
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
# Prerequisites: Docker running, research_advisor_postgres container exists (docker compose up -d).

set -e

CONTAINER="research_advisor_postgres"
LOCAL_DB="research_advisor"
DUMP_FILE="gap_map_data.sql"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load Supabase URL from .env (Session Pooler)
SUPABASE_URL=$(grep -E '^DATABASE_URL=' "$PROJECT_ROOT/.env" 2>/dev/null | cut -d= -f2- || true)

if [ -z "$SUPABASE_URL" ]; then
  echo "Error: DATABASE_URL not found in .env"
  exit 1
fi

# Convert asyncpg URL to psql format (postgresql://)
PSQL_URL="${SUPABASE_URL/postgresql+asyncpg:/postgresql:}"

echo "1. Checking Docker container..."
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "   Container '$CONTAINER' not running. Start with: docker compose up -d"
  exit 1
fi

echo "2. Dumping gap_map_entries from local PostgreSQL..."
docker exec "$CONTAINER" pg_dump -U postgres -d "$LOCAL_DB" \
  --data-only \
  --table=gap_map_entries \
  --column-inserts \
  > "$PROJECT_ROOT/$DUMP_FILE"

if [ ! -s "$PROJECT_ROOT/$DUMP_FILE" ]; then
  echo "   Warning: Dump file is empty. Table may be empty."
  rm -f "$PROJECT_ROOT/$DUMP_FILE"
  exit 1
fi

echo "   Dumped to $DUMP_FILE ($(wc -l < "$PROJECT_ROOT/$DUMP_FILE") lines)"

echo "3. Truncating Supabase gap_map_entries (to avoid conflicts)..."
psql "$PSQL_URL" -c "TRUNCATE gap_map_entries RESTART IDENTITY CASCADE;" -v ON_ERROR_STOP=1

echo "4. Importing into Supabase..."
psql "$PSQL_URL" -f "$PROJECT_ROOT/$DUMP_FILE" -v ON_ERROR_STOP=1

echo "5. Cleaning up..."
rm -f "$PROJECT_ROOT/$DUMP_FILE"

echo "Done. Verify in Supabase: SELECT COUNT(*) FROM gap_map_entries;"
