
# SCHOOL AI ASSISTANT

Startup-grade AI-powered education platform scaffold with:
- Next.js + TypeScript + Tailwind frontend
- FastAPI + SQLAlchemy backend
- PostgreSQL data layer
- JWT auth
- Modular AI service architecture
- Real-time WebSocket study rooms

This repository is local-first. Default placeholder domain:
- `https://schoolaiassistant.local`

You can later replace it with a purchased domain such as:
- `schoolaiassistant.com`
- `schoolaiassistant.co`
- `schoolaiassistant.ai`

## 1) Tech Stack Choice (Why)

### Frontend
- **Next.js App Router + React + TypeScript**: fast iteration, production-grade routing/layouts, scalable code organization.
- **Tailwind CSS**: rapid premium UI implementation with consistent design tokens.

### Backend
- **FastAPI**: high-performance Python API framework with typed contracts.
- **SQLAlchemy ORM**: production-ready relational modeling, migration-friendly.
- **JWT Auth**: simple secure MVP auth that can expand to OAuth providers.

### Database
- **PostgreSQL**: production-ready relational data for users, sessions, analytics, and collaboration.

### Real-time
- **WebSockets** for live study room presence and chat.

### AI Architecture
- Provider interface (`AIProvider`) + pluggable implementations.
- Current provider: `MockAIProvider`.
- Future providers can be added without rewriting endpoint logic.

## 2) Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   ├── router.py
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── ai/
│   │   │   ├── analytics/
│   │   │   ├── collab/
│   │   │   └── planner/
│   │   ├── ws/
│   │   └── main.py
│   ├── .env.example
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   ├── dashboard/
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   ├── .env.example
│   └── package.json
├── infra/
│   └── docker-compose.yml
├── docs/
│   └── DEPLOYMENT.md
└── .env.example
```

## 3) Frontend Coverage

Implemented pages:
- Landing page (`/`): hero, feature highlights, how-it-works, testimonials placeholder, FAQ placeholder, footer.
- Auth pages: `/login`, `/signup`.
- Dashboard and modules:
  - `/dashboard`
  - `/dashboard/homework`
  - `/dashboard/flashcards`
  - `/dashboard/tutor`
  - `/dashboard/planner`
  - `/dashboard/exams`
  - `/dashboard/analytics`
  - `/dashboard/study-room`
  - `/dashboard/settings`

## 4) Backend API Coverage

Implemented API groups (`/api/v1`):
- `auth`: signup, login, me
- `users`: profile read/update
- `homework`: solve, file solve, progressive hints, whiteboard placeholder, practice generation
- `flashcards`: deck generation
- `tutor`: tutor chat
- `planner`: study plan generation + task listing
- `exams`: generate + submit/grade
- `analytics`: dashboard, confusion signals, memory schedule queue, knowledge graph
- `learning`: lecture summarizer, explain mistake, learning style, mistake patterns, gap scan
- `study-rooms`: create/list/invite/join/messages

WebSocket endpoint:
- `/ws/rooms/{room_id}` for chat + presence broadcasts.

## 5) Data Models

Schema includes:
- users
- user_profiles
- study_buddy_state
- homework_requests
- generated_solutions
- practice_sets
- flashcard_decks
- flashcards
- exam_simulations
- exam_questions
- analytics_snapshots
- knowledge_graph_nodes
- memory_review_schedule
- planner_tasks
- study_rooms
- room_memberships
- room_messages
- room_invites

## 6) AI Engine Modules

- Interface: `backend/app/services/ai/base.py`
- Provider factory: `backend/app/services/ai/factory.py`
- Current implementation: `backend/app/services/ai/mock_provider.py`

Capabilities exposed through interface:
- solve problems
- explanation styles
- hints
- practice generation
- flashcard generation
- lecture summarization
- tutor chat
- mistake analysis
- study plan generation
- learning style detection
- knowledge gap scan

## 7) Collaboration / Real-Time

- Room creation + membership + invite acceptance.
- Hard cap enforcement: 5 participants per room (host + 4 invited).
- WebSocket room broadcast channel for chat/presence.

## 8) Configuration

- Root: `.env.example`
- Backend: `backend/.env.example`
- Frontend: `frontend/.env.example`

Important variables:
- `APP_NAME`
- `SITE_URL`
- `API_URL`
- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_API_URL`
- `DATABASE_URL`
- `JWT_SECRET`
- `AI_PROVIDER`

## 9) Local Setup and Run

Prerequisites:
- Node.js 20+
- npm 10+
- Python 3.11+
- PostgreSQL 16+ (or Docker)

### A. Start database
Option 1 (Docker):
```bash
cd infra
docker compose up -d
```

Option 2 (local PostgreSQL):
- create database `school_ai_assistant`
- set `DATABASE_URL` in `backend/.env`

### B. Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL:
- `http://localhost:8000`
- Health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### C. Frontend
```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Frontend URL:
- `http://localhost:3000`

Local app flow:
1. Open `http://localhost:3000`
2. Sign up at `/signup`
3. Use dashboard modules

## 10) Production Deployment Guidance

Detailed guide: `docs/DEPLOYMENT.md`.

High-level:
1. Provision PostgreSQL and set secure `DATABASE_URL`.
2. Deploy backend as container or VM service (Uvicorn/Gunicorn).
3. Deploy frontend on Vercel, Netlify, or container hosting.
4. Configure CORS between frontend domain and backend API domain.
5. Set `SITE_URL` and `NEXT_PUBLIC_SITE_URL` to your real domain.
6. Add TLS certificates and enforce HTTPS.
7. Replace mock AI provider with production model integration.

## Placeholder vs Implemented

Implemented:
- full-stack scaffolding, auth, database models, core APIs, UI pages, real-time architecture.

Placeholder-ready (intentional for MVP phase 1):
- production LLM provider integration
- OCR/handwriting recognition in whiteboard solver
- full migration workflow (Alembic placeholder notes included)
- advanced telemetry ingestion pipelines
