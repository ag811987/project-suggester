# Railway Deployment

## Prerequisites

1. **Railway CLI** (installed as project dev dependency): `npm install` from project root
2. **Railway login**: `npx railway login` (opens browser)
3. **Redis**: Add Redis to your Railway project first (Dashboard: + New > Database > Redis)
4. **.env** with: `OPENAI_API_KEY`, `OPENALEX_EMAIL`, `DATABASE_URL`, `REDIS_URL`

## DATABASE_URL

Use Supabase Session Pooler with asyncpg driver:

```
postgresql+asyncpg://postgres.begpcydtxgltgznzdwch:[YOUR-PASSWORD]@aws-1-us-east-1.pooler.supabase.com:5432/postgres
```

## REDIS_URL

After adding Redis to your Railway project, copy `REDIS_URL` from the Redis service's Variables tab.

## Deploy Steps

1. **Login** (one-time):
   ```bash
   cd research-advisor-backend
   npx railway login
   ```

2. **Link or create project**:
   ```bash
   npx railway link   # or: npx railway init
   ```

3. **Set Root Directory** (if monorepo): In Railway Dashboard > Service > Settings > Root Directory = `research-advisor-backend`

4. **Add Redis** (manual): Dashboard > + New > Database > Redis

5. **Set variables** (from .env or manually):
   ```bash
   npx railway variable set \
     "DATABASE_URL=postgresql+asyncpg://postgres.begpcydtxgltgznzdwch:PASSWORD@aws-1-us-east-1.pooler.supabase.com:5432/postgres" \
     "REDIS_URL=redis://..." \
     "OPENAI_API_KEY=sk-..." \
     "OPENALEX_EMAIL=your@email.com" \
     "CORS_ORIGINS=*" \
     "ENVIRONMENT=production"
   ```

6. **Deploy**:
   ```bash
   npx railway up
   ```

7. **Generate domain**:
   ```bash
   npx railway domain
   ```

## One-command deploy (script)

If `.env` has all required vars:

```bash
npm run railway:deploy
```

From project root. Requires `railway login` and Redis added first.

## MCP Note

Railway MCP tools require the Railway CLI to be in your PATH. Install globally: `npm i -g @railway/cli` or ensure `npx railway` works from the project directory.
