# Architecture Overview

## Core Layers

1. Frontend (`frontend/src/app`)
- Next.js App Router pages for marketing, auth, dashboard modules.
- Reusable UI primitives under `components/ui`.
- Layout primitives under `components/layout`.

2. Backend API (`backend/app/api`)
- Route groups by domain (auth, homework, planner, analytics, study rooms, etc.).
- Shared auth dependency (`get_current_user`) for protected routes.

3. Domain Models (`backend/app/models`)
- SQLAlchemy models covering users, content generation, analytics, memory scheduling, and collaboration.

4. AI Service Layer (`backend/app/services/ai`)
- Provider abstraction interface.
- Provider factory for runtime selection.
- Mock provider now, production provider later.

5. Real-Time Collaboration (`backend/app/ws`)
- Room-scoped websocket connection manager.
- Presence and chat broadcasts.

## Evolution Path

- Add Alembic migrations and remove runtime `create_all()`.
- Add production AI provider and background workers for heavy tasks.
- Add object storage for uploaded files (PDF/images/audio/video).
- Add Redis for websocket scaling and ephemeral collaboration state.
