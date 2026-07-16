from fastapi import APIRouter, Depends
from app.api.v1.responses import SuccessResponse, create_response
from app.application.student_service import StudentService
from app.api.v1.dependencies import get_uow, get_current_student
from app.repositories.base.unit_of_work import UnitOfWork

router = APIRouter(prefix="/student", tags=["Student"])

@router.get("/profile", response_model=SuccessResponse)
def get_profile(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = StudentService(uow)
    data = service.get_profile(student.id)
    return create_response(data, "Profile retrieved successfully")

@router.get("/progress", response_model=SuccessResponse)
def get_progress(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = StudentService(uow)
    data = service.get_progress(student.id)
    return create_response(data, "Progress retrieved successfully")

from app.schemas.student.requests import DailyCheckinRequest

@router.post("/daily-checkin", response_model=SuccessResponse)
def daily_checkin(request: DailyCheckinRequest, student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = StudentService(uow)
    service.set_daily_learning(student.id, request.learning_date, request.topic_ids, request.source)
    return create_response({}, "Daily learning recorded successfully")
