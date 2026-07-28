from fastapi import APIRouter, Depends
import uuid
from app.api.v1.responses import SuccessResponse, create_response
from app.application.content_service import ContentService
from app.api.v1.dependencies import get_uow, get_current_student
from app.repositories.base.unit_of_work import UnitOfWork

router = APIRouter(prefix="/content", tags=["Content"])

@router.get("/subjects", response_model=SuccessResponse)
def get_subjects(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = ContentService(uow)
    data = service.get_subjects(student.id)
    return create_response(data, "Subjects retrieved successfully")

@router.get("/chapters", response_model=SuccessResponse)
def get_chapters(subject_id: uuid.UUID, student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = ContentService(uow)
    data = service.get_chapters(student.id, subject_id)
    return create_response(data, "Chapters retrieved successfully")

@router.get("/curriculum", response_model=SuccessResponse)
def get_full_curriculum(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = ContentService(uow)
    data = service.get_full_curriculum(student.id)
    return create_response(data, "Curriculum retrieved successfully")
