from pydantic import EmailStr, Field, BaseModel
from typing import Optional
import uuid
from app.schemas.common.base import CamelBaseModel

class RegisterRequest(CamelBaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)
    grade_id: Optional[uuid.UUID] = None
    board_id: Optional[uuid.UUID] = None

class LoginRequest(CamelBaseModel):
    email: EmailStr
    password: str

class SocialLoginRequest(CamelBaseModel):
    provider: str
    provider_token: str

class RefreshTokenRequest(CamelBaseModel):
    refresh_token: str

class LogoutRequest(CamelBaseModel):
    device_id: Optional[str] = None  # If provided, only deactivate that device's token

class AuthResponse(BaseModel):
    student_id: uuid.UUID
    access_token: str
    refresh_token: str
    role: str

class LoginResponse(BaseModel):
    student_id: uuid.UUID
    name: str
    access_token: str
    refresh_token: str
    role: str

class RefreshTokenResponse(BaseModel):
    student_id: uuid.UUID
    access_token: str
    refresh_token: str

class UserMeResponse(BaseModel):
    student_id: uuid.UUID
    email: EmailStr
    name: str
    role: str
