# Deployment Guide (Free MVP-first)

For fastest free deployment, use:
- Backend: Render free web service
- Frontend: Vercel free tier
- Database: SQLite

Follow the exact checklist in:
- `docs/QUICK_DEPLOY_FREE.md`

## Why this path
- No paid infrastructure
- No separate database setup required
- Beginner-friendly environment variable flow
- Public URL for both frontend and backend

## Important free-tier note
- Render free instances may sleep; first request can be slow.
- SQLite data can reset on redeploy/restart in ephemeral environments.

## Later hardening
- Move to managed Postgres
- Add Alembic migrations
- Add production AI provider
