from fastapi import APIRouter, Depends

from app.api.v1.responses import SuccessResponse, create_response
from app.api.v1.dependencies import get_uow, get_current_student
from app.repositories.base.unit_of_work import UnitOfWork
from app.schemas.notification.notification_schema import RegisterDeviceTokenRequest

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/register-token", response_model=SuccessResponse)
def register_device_token(
    request: RegisterDeviceTokenRequest,
    student=Depends(get_current_student),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Register or update a FCM/APN device token for push notifications.
    Called by the mobile app after login or when the token refreshes.
    """
    with uow:
        uow.device_tokens.upsert_token(
            student_id=student.id,
            token=request.token,
            platform=request.platform.lower(),
            device_id=request.device_id,
        )
        uow.commit()

    return create_response({}, "Device token registered successfully")
