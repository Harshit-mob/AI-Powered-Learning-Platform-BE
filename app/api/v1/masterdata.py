from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
import uuid
from app.api.v1.responses import SuccessResponse, GenericSuccessResponse, create_response
from app.api.v1.errors import APIException
from app.application.masterdata_service import MasterdataService
from app.api.v1.dependencies import get_uow, get_current_admin
from app.repositories.base.unit_of_work import UnitOfWork
from app.schemas.masterdata_schema import (
    MasterdataItemResponse,
    BoardCreate,
    BoardUpdate,
    BoardResponse,
    GradeCreate,
    GradeUpdate,
    GradeResponse,
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse
)

router = APIRouter(prefix="/masterdata", tags=["Masterdata"])

# --- Board Endpoints ---
@router.get("/boards", response_model=GenericSuccessResponse[List[MasterdataItemResponse]])
def get_boards(uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    data = service.get_boards()
    return create_response(data, "Boards retrieved successfully")


@router.post("/boards", response_model=GenericSuccessResponse[BoardResponse], status_code=status.HTTP_201_CREATED)
def create_board(payload: BoardCreate, admin = Depends(get_current_admin), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    board = service.create_board(name=payload.name)
    return create_response(board, "Board created successfully")

@router.put("/boards/{board_id}", response_model=GenericSuccessResponse[BoardResponse])
def update_board(board_id: uuid.UUID, payload: BoardUpdate, admin = Depends(get_current_admin), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    board = service.update_board(board_id, name=payload.name)
    if not board:
        raise APIException("NOT_FOUND", f"Board with ID {board_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    return create_response(board, "Board updated successfully")

@router.delete("/boards/{board_id}", response_model=GenericSuccessResponse[bool])
def delete_board(board_id: uuid.UUID, admin = Depends(get_current_admin), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    success = service.delete_board(board_id)
    if not success:
        raise APIException("NOT_FOUND", f"Board with ID {board_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    return create_response(True, "Board deleted successfully")




@router.get("/boards/{board_id}/grades", response_model=GenericSuccessResponse[List[MasterdataItemResponse]])
def get_grades_by_board(board_id: uuid.UUID, uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    data = service.get_grades_by_board(board_id)
    return create_response(data, "Grades retrieved successfully")




@router.post("/grades", response_model=GenericSuccessResponse[GradeResponse], status_code=status.HTTP_201_CREATED)
def create_grade(payload: GradeCreate, admin = Depends(get_current_admin), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    # Check if board exists
    board = service.get_board(payload.board_id)
    if not board:
        raise APIException("NOT_FOUND", f"Parent Board with ID {payload.board_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    grade = service.create_grade(board_id=payload.board_id, name=payload.name)
    return create_response(grade, "Grade created successfully")

@router.put("/grades/{grade_id}", response_model=GenericSuccessResponse[GradeResponse])
def update_grade(grade_id: uuid.UUID, payload: GradeUpdate, admin = Depends(get_current_admin), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    if payload.board_id:
        board = service.get_board(payload.board_id)
        if not board:
            raise APIException("NOT_FOUND", f"Parent Board with ID {payload.board_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    grade = service.update_grade(grade_id, board_id=payload.board_id, name=payload.name)
    if not grade:
        raise APIException("NOT_FOUND", f"Grade with ID {grade_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    return create_response(grade, "Grade updated successfully")

@router.delete("/grades/{grade_id}", response_model=GenericSuccessResponse[bool])
def delete_grade(grade_id: uuid.UUID, admin = Depends(get_current_admin), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    success = service.delete_grade(grade_id)
    if not success:
        raise APIException("NOT_FOUND", f"Grade with ID {grade_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    return create_response(True, "Grade deleted successfully")


# --- Subject Endpoints ---
@router.get("/subjects", response_model=GenericSuccessResponse[List[SubjectResponse]])
def get_subjects(grade_id: Optional[uuid.UUID] = Query(None), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    if grade_id:
        data = service.get_subjects_by_grade(grade_id)
    else:
        data = service.get_all_subjects()
    return create_response(data, "Subjects retrieved successfully")


@router.post("/subjects", response_model=GenericSuccessResponse[SubjectResponse], status_code=status.HTTP_201_CREATED)
def create_subject(payload: SubjectCreate, admin = Depends(get_current_admin), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    # Check if grade exists
    grade = service.get_grade(payload.grade_id)
    if not grade:
        raise APIException("NOT_FOUND", f"Parent Grade with ID {payload.grade_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    subject = service.create_subject(grade_id=payload.grade_id, name=payload.name)
    return create_response(subject, "Subject created successfully")

@router.put("/subjects/{subject_id}", response_model=GenericSuccessResponse[SubjectResponse])
def update_subject(subject_id: uuid.UUID, payload: SubjectUpdate, admin = Depends(get_current_admin), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    if payload.grade_id:
        grade = service.get_grade(payload.grade_id)
        if not grade:
            raise APIException("NOT_FOUND", f"Parent Grade with ID {payload.grade_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    subject = service.update_subject(subject_id, grade_id=payload.grade_id, name=payload.name)
    if not subject:
        raise APIException("NOT_FOUND", f"Subject with ID {subject_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    return create_response(subject, "Subject updated successfully")

@router.delete("/subjects/{subject_id}", response_model=GenericSuccessResponse[bool])
def delete_subject(subject_id: uuid.UUID, admin = Depends(get_current_admin), uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    success = service.delete_subject(subject_id)
    if not success:
        raise APIException("NOT_FOUND", f"Subject with ID {subject_id} not found", status_code=status.HTTP_404_NOT_FOUND)
    return create_response(True, "Subject deleted successfully")

