# Alembic placeholder

This project currently auto-creates tables at startup for fast MVP iteration.

Production recommendation:
1. Initialize Alembic in `backend/`.
2. Generate and review schema migrations.
3. Disable runtime `create_all()` and rely on migration pipeline.
