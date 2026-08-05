from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
from typing import Generator

from app.database.session import SessionLocal
from app.repositories.base.unit_of_work import UnitOfWork
from app.api.v1.auth_utils import decode_token
from app.api.v1.errors import APIException

security = HTTPBearer()

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_uow(db = Depends(get_db)) -> UnitOfWork:
    return UnitOfWork(lambda: db)

def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    uow: UnitOfWork = Depends(get_uow)
):
    token = credentials.credentials
    student_id = decode_token(token)
    
    if not student_id:
        raise APIException("UNAUTHORIZED", "Invalid or expired token", 401)
        
    try:
        uid = uuid.UUID(student_id)
    except ValueError:
        raise APIException("UNAUTHORIZED", "Invalid token subject", 401)
        
    with uow:
        student = uow.students.find_by_id(uid)
        if not student:
            raise APIException("UNAUTHORIZED", "User not found", 401)
            
        # Optional: check if user is active, etc.
        return student

def get_current_admin(
    student = Depends(get_current_student)
):
    if getattr(student, "role", "STUDENT") != "ADMIN":
        raise APIException("FORBIDDEN", "Admin access required", 403)
    return student
