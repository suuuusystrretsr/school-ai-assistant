# Quick Free Deployment Guide (GitHub + Render + Vercel)

This guide gets you a public website your friends can use.

## 1) Push to GitHub

1. Create a new GitHub repo (public or private).
2. In project root, run:
```bash
git init
git add .
git commit -m "Prepare SCHOOL AI ASSISTANT for free public deployment"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
git push -u origin main
```

## 2) Deploy Backend to Render (Free)

1. Go to [render.com](https://render.com) and sign in.
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repo.
4. Render detects `render.yaml`; deploy service.
5. Wait for deploy. You get a backend URL like:
   - `https://school-ai-assistant-api.onrender.com`

### Backend Environment Variables (Render)
Set or verify:
- `APP_NAME=SCHOOL AI ASSISTANT API`
- `ENV=production`
- `API_PREFIX=/api/v1`
- `API_URL=https://<YOUR-RENDER-SERVICE>.onrender.com/api/v1`
- `SITE_URL=https://<YOUR-VERCEL-DOMAIN>.vercel.app`
- `CORS_ORIGINS=https://<YOUR-VERCEL-DOMAIN>.vercel.app`
- `DATABASE_URL=sqlite:///./school_ai_assistant.db`
- `JWT_SECRET=<click Generate in Render or set random long string>`
- `JWT_ALGORITHM=HS256`
- `JWT_EXPIRES_MINUTES=10080`
- `AI_PROVIDER=mock` (or `huggingface`)
- `AI_MODEL=mock-edu-v1`
- `HF_API_KEY=<YOUR_HF_TOKEN>`
- `HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct`

Test backend:
- `https://<YOUR-RENDER-SERVICE>.onrender.com/health`
- `https://<YOUR-RENDER-SERVICE>.onrender.com/docs`

## 3) Deploy Frontend to Vercel (Free)

1. Go to [vercel.com](https://vercel.com) and sign in.
2. Click **Add New Project** and import your GitHub repo.
3. Set **Root Directory** to `frontend`.
4. Add environment variables:
   - `NEXT_PUBLIC_APP_NAME=SCHOOL AI ASSISTANT`
   - `NEXT_PUBLIC_SITE_URL=https://<YOUR-VERCEL-DOMAIN>.vercel.app`
   - `NEXT_PUBLIC_API_URL=https://<YOUR-RENDER-SERVICE>.onrender.com/api/v1`
   - `NEXT_PUBLIC_WS_URL=wss://<YOUR-RENDER-SERVICE>.onrender.com`
5. Deploy.

## 4) Connect Frontend + Backend

After frontend deploy, copy Vercel URL and paste into Render backend env:
- `SITE_URL`
- `CORS_ORIGINS`

Redeploy backend once after updating env vars.

## 5) Final Public Test

1. Open frontend URL from phone (mobile data) and from another computer.
2. Test:
   - Landing page loads
   - Sign up and login
   - Dashboard pages open
   - Homework solve
   - Tutor chat
   - Planner generate
   - Flashcards generate
3. Optional study room test:
   - Open two browser tabs, same room id, connect WS, send messages.

## 6) Known MVP Simplifications

- SQLite used for speed and zero-cost setup.
- AI is mock provider for stable free demo behavior.
- If WebSocket connection is unstable on free tier, app core still works.

## 7) Upgrade Path (Later)

- Switch `DATABASE_URL` to managed Postgres.
- Add production LLM provider in AI service factory.
- Add persistent storage for uploaded files.



