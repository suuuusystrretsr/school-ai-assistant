from fastapi import APIRouter

from app.api.routes import analytics, auth, exams, flashcards, homework, learning, planner, study_rooms, tutor, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(homework.router)
api_router.include_router(flashcards.router)
api_router.include_router(tutor.router)
api_router.include_router(planner.router)
api_router.include_router(exams.router)
api_router.include_router(analytics.router)
api_router.include_router(learning.router)
api_router.include_router(study_rooms.router)
