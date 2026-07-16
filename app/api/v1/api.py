from fastapi import APIRouter
from app.api.v1.endpoints import course, quiz

api_router = APIRouter()
# We include the course router and give it a clean prefix
api_router.include_router(course.router, prefix="/course", tags=["course"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
