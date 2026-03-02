#!/bin/bash
# Railway deploy script - run after: npm i -g @railway/cli && railway login
# Requires: Railway CLI installed, .env with OPENAI_API_KEY, OPENALEX_EMAIL, DATABASE_URL, REDIS_URL

set -e
cd "$(dirname "$0")/.."

# Load .env from project root or backend dir
if [ -f ../.env ]; then
  set -a
  source ../.env
  set +a
elif [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Check required vars
for var in OPENAI_API_KEY OPENALEX_EMAIL DATABASE_URL REDIS_URL; do
  if [ -z "${!var}" ]; then
    echo "Error: $var not set. Add to .env or export before running."
    exit 1
  fi
done

# Ensure DATABASE_URL uses asyncpg driver
if [[ "$DATABASE_URL" != *"asyncpg"* ]]; then
  DATABASE_URL="${DATABASE_URL/postgresql:\/\//postgresql+asyncpg:\/\/}"
fi

echo "Linking project (creates if new)..."
npx railway link || npx railway init

echo "Setting variables..."
npx railway variable set \
  "DATABASE_URL=$DATABASE_URL" \
  "REDIS_URL=$REDIS_URL" \
  "OPENAI_API_KEY=$OPENAI_API_KEY" \
  "OPENALEX_EMAIL=$OPENALEX_EMAIL" \
  "CORS_ORIGINS=*" \
  "ENVIRONMENT=production"

echo "Deploying..."
npx railway up

echo "Generating domain..."
npx railway domain

echo "Done. Get your URL from: npx railway status"
