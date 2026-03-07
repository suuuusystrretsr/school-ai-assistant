# Production Deployment Guide - SCHOOL AI ASSISTANT

## 1. Domain Strategy

Start with placeholder domain values in config:
- `https://schoolaiassistant.local`

When you buy a real domain (example `schoolaiassistant.com`), update:
- Backend: `SITE_URL`
- Frontend: `NEXT_PUBLIC_SITE_URL`
- Any reverse proxy host rules

## 2. Recommended Topology

- Frontend: Next.js app (`frontend`) on Vercel or container host
- Backend API: FastAPI (`backend`) on Fly.io/Render/Railway/Docker host
- Database: Managed PostgreSQL
- Optional Redis for queues/session expansion later

## 3. Backend Deployment

### Environment variables
- `APP_NAME=SCHOOL AI ASSISTANT API`
- `ENV=production`
- `API_PREFIX=/api/v1`
- `SITE_URL=https://app.schoolaiassistant.com`
- `DATABASE_URL=postgresql+psycopg2://...`
- `JWT_SECRET=<secure-random-secret>`
- `CORS_ORIGINS=https://schoolaiassistant.com,https://app.schoolaiassistant.com`
- `AI_PROVIDER=mock` (replace later)

### Run command
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For scale, run behind process manager or Gunicorn/Uvicorn workers.

## 4. Frontend Deployment

### Environment variables
- `NEXT_PUBLIC_APP_NAME=SCHOOL AI ASSISTANT`
- `NEXT_PUBLIC_SITE_URL=https://schoolaiassistant.com`
- `NEXT_PUBLIC_API_URL=https://api.schoolaiassistant.com/api/v1`

### Build and run
```bash
npm install
npm run build
npm run start
```

## 5. Reverse Proxy and SSL

- Put frontend and backend behind HTTPS.
- Suggested subdomains:
  - `schoolaiassistant.com` -> frontend
  - `api.schoolaiassistant.com` -> backend
- Enforce HSTS and HTTP -> HTTPS redirects.

## 6. Database and Migrations

Current MVP auto-creates tables at API startup.

For production hardening:
1. Initialize Alembic.
2. Generate migration from current models.
3. Run migrations in CI/CD before app release.
4. Remove runtime `create_all()`.

## 7. AI Provider Upgrade Path

Current provider is mock for deterministic MVP.

Upgrade plan:
1. Add new provider class implementing `AIProvider`.
2. Add provider selection in `factory.py`.
3. Set `AI_PROVIDER` and secure API keys.
4. Add rate limits and model fallback logic.

## 8. Security Baseline

- Strong `JWT_SECRET` and rotation policy.
- Add request rate limiting at API gateway/proxy.
- Add audit logging for auth and high-risk endpoints.
- Add content moderation checks for user uploads in phase 2.

## 9. Observability

- Add centralized logs (structured JSON logs recommended).
- Add metrics (p95 latency, error rates, websocket connections).
- Add alerting for database failures and elevated auth errors.

## 10. Launch Checklist

- [ ] Domain + DNS configured
- [ ] TLS enabled
- [ ] Production secrets configured
- [ ] CORS set for real domains
- [ ] Health checks + monitoring enabled
- [ ] Backup policy for PostgreSQL
- [ ] Load test key API routes
- [ ] Replace mock AI provider for production
