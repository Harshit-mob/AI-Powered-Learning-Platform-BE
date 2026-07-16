from fastapi import APIRouter, Depends
import uuid
from app.api.v1.responses import SuccessResponse, create_response
from app.application.masterdata_service import MasterdataService
from app.api.v1.dependencies import get_uow
from app.repositories.base.unit_of_work import UnitOfWork

router = APIRouter(prefix="/masterdata", tags=["Masterdata"])

@router.get("/boards", response_model=SuccessResponse)
def get_boards(uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    data = service.get_boards()
    return create_response(data, "Boards retrieved successfully")

@router.get("/boards/{board_id}/grades", response_model=SuccessResponse)
def get_grades_by_board(board_id: uuid.UUID, uow: UnitOfWork = Depends(get_uow)):
    service = MasterdataService(uow)
    data = service.get_grades_by_board(board_id)
    return create_response(data, "Grades retrieved successfully")
