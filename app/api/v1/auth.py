from fastapi import APIRouter, Depends
from app.api.v1.responses import SuccessResponse, GenericSuccessResponse, create_response
from app.schemas.auth.auth_schema import (
    RegisterRequest,
    LoginRequest,
    SocialLoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    AuthResponse,
    LoginResponse,
    RefreshTokenResponse,
    UserMeResponse
)
from app.application.auth_service import AuthService
from app.api.v1.dependencies import get_uow, get_current_student
from app.repositories.base.unit_of_work import UnitOfWork

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=GenericSuccessResponse[AuthResponse])
def register(request: RegisterRequest, uow: UnitOfWork = Depends(get_uow)):
    service = AuthService(uow)
    data = service.register_student(request.model_dump())
    return create_response(data, "Registration successful")

@router.post("/login", response_model=GenericSuccessResponse[LoginResponse])
def login(request: LoginRequest, uow: UnitOfWork = Depends(get_uow)):
    service = AuthService(uow)
    data = service.login_student(request.model_dump())
    return create_response(data, "Login successful")

@router.post("/social-login", response_model=GenericSuccessResponse[AuthResponse])
def social_login(request: SocialLoginRequest, uow: UnitOfWork = Depends(get_uow)):
    service = AuthService(uow)
    data = service.social_login(request.provider, request.provider_token)
    return create_response(data, f"{request.provider.capitalize()} login successful")

@router.post("/refresh", response_model=GenericSuccessResponse[RefreshTokenResponse])
def refresh_token(request: RefreshTokenRequest, uow: UnitOfWork = Depends(get_uow)):
    service = AuthService(uow)
    data = service.refresh_access_token(request.refresh_token)
    return create_response(data, "Tokens refreshed successfully")

@router.post("/logout", response_model=SuccessResponse)
def logout(
    request: LogoutRequest,
    student=Depends(get_current_student),
    uow: UnitOfWork = Depends(get_uow),
):
    with uow:
        if request.device_id:
            # Deactivate only the token for this specific device
            uow.device_tokens.deactivate_by_device(student.id, request.device_id)
        else:
            # No device_id provided — deactivate all tokens for this student
            uow.device_tokens.deactivate_all_for_student(student.id)
        uow.commit()
    return create_response({}, "Logged out successfully")

@router.get("/me", response_model=GenericSuccessResponse[UserMeResponse])
def get_me(student = Depends(get_current_student)):
    return create_response({"student_id": str(student.id), "email": student.email, "name": student.name, "role": getattr(student, "role", "STUDENT")})
