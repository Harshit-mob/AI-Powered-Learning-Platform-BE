from fastapi import APIRouter, Depends
from app.api.v1.responses import SuccessResponse, GenericSuccessResponse, create_response
from app.application.home_service import HomeService
from app.api.v1.dependencies import get_uow, get_current_student
from app.repositories.base.unit_of_work import UnitOfWork
from app.schemas.home_schema import HomeDashboardResponse

router = APIRouter(prefix="/home", tags=["Home"])

@router.get("", response_model=GenericSuccessResponse[HomeDashboardResponse])
def get_home(student = Depends(get_current_student), uow: UnitOfWork = Depends(get_uow)):
    service = HomeService(uow)
    data = service.get_home_dashboard(student.id)
    return create_response(data, "Home dashboard retrieved successfully")
