# SCHOOL AI ASSISTANT (Fast Public MVP)

This repo is now optimized for **fast free deployment**:
- Frontend: **Vercel free tier**
- Backend: **Render free tier**
- Database: **SQLite** (no external DB setup required)

## Local Quick Start

### Backend
```bash
cd backend
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Open:
- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

## Free Public Deployment (Beginner Path)

Follow:
- `docs/QUICK_DEPLOY_FREE.md` (full exact steps)

## Platform Config Files Included

- `render.yaml` (Render backend blueprint)
- `frontend/next.config.mjs` (Vercel Next.js config)
- `frontend/src/app/api/proxy/[...path]/route.ts` (Vercel backend proxy)
- `.env.example`, `backend/.env.example`, `frontend/.env.example`

## Notes

- SQLite is used by default for fastest launch.
- Data on free backend instances may reset on restarts/redeploys.
- WebSocket study room still works; if host limits WebSockets, core app remains usable.

## Enable Free Smarter AI (Hugging Face)

Set these in **Render backend env vars**:
- `AI_PROVIDER=huggingface`
- `HF_API_KEY=<your_hf_token>`
- `HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct`
- `HF_TIMEOUT_SECONDS=35`
- `HF_MAX_NEW_TOKENS=500`

After redeploy, verify:
- `https://<your-render-app>/health` returns `effective_ai_provider: huggingface`

## Upgrade Later

- Move DB to managed Postgres.
- Add stronger AI provider in `backend/app/services/ai/factory.py`.
- Add persistent object storage for uploads.
