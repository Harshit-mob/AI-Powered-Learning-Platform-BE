from fastapi import APIRouter, Depends
from typing import List
import uuid
from app.api.v1.responses import SuccessResponse, GenericSuccessResponse, create_response
from app.schemas.session.session_schema import (
    SessionGenerateRequest,
    AnswerSubmissionRequest,
    SessionCompleteResponse,
    SessionGenerateResponse,
    AnswerResponse,
    RecommendationCard
)
from app.application.session_service import SessionApplicationService
from app.api.v1.dependencies import get_uow, get_current_student
from app.repositories.base.unit_of_work import UnitOfWork

router = APIRouter(prefix="/session", tags=["Session"])

@router.post("/generate", response_model=GenericSuccessResponse[SessionGenerateResponse])
def generate_session(request: SessionGenerateRequest, student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = SessionApplicationService(uow)
    payload = {}
    if request.scope.upper() == "TOPIC":
        payload["topic_ids"] = request.ids
    elif request.scope.upper() == "CHAPTER":
        payload["chapter_ids"] = request.ids
    elif request.scope.upper() == "MULTI_TOPIC":
        payload["multi_topic_ids"] = request.ids
    elif request.scope.upper() == "STUDENT":
        payload["student_ids"] = request.ids
        
    payload["session_type"] = request.session_type
    data = service.generate_session(student.id, payload)
    return create_response(data, "Session generated successfully")

@router.post("/answer", response_model=GenericSuccessResponse[AnswerResponse])
def submit_answer(request: AnswerSubmissionRequest, student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = SessionApplicationService(uow)
    data = service.answer_question(student.id, request.model_dump())
    return create_response(data, "Answer processed successfully")

@router.post("/{session_id}/complete", response_model=GenericSuccessResponse[SessionCompleteResponse])
def complete_session(session_id: uuid.UUID, student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = SessionApplicationService(uow)
    data = service.complete_session(student.id, session_id)
    return create_response(data, "Session completed successfully")

@router.get("/recommendations", response_model=GenericSuccessResponse[List[RecommendationCard]])
def get_recommendations(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = SessionApplicationService(uow)
    data = service.get_session_recommendations(student.id)
    return create_response(data, "Recommendations retrieved successfully")

@router.get("/{session_id}", response_model=GenericSuccessResponse[SessionGenerateResponse])
def resume_session(session_id: uuid.UUID, student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = SessionApplicationService(uow)
    data = service.resume_session(student.id, session_id)
    return create_response(data, "Session resumed successfully")
