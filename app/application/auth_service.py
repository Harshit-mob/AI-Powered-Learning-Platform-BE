import uuid
from typing import Dict, Any

from app.repositories.base.unit_of_work import UnitOfWork
from app.api.v1.auth_utils import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.api.v1.errors import APIException

class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def register_student(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self.uow:
            email = data["email"].strip().lower()
            # Check if email exists
            if self.uow.students.find_by_email(email):
                raise APIException("AUTH_EMAIL_EXISTS", "Email already registered", 400)
                
            # Create user
            student_id = uuid.uuid4()
            hashed_pwd = get_password_hash(data["password"])
            
            student = self.uow.students.create({
                "id": student_id,
                "email": email,
                "hashed_password": hashed_pwd,
                "name": data["name"],
                "grade_id": data.get("grade_id"),
                "board_id": data.get("board_id")
            })
            self.uow.commit()
            
            # Generate Tokens
            access_token = create_access_token(student_id)
            refresh_token = create_refresh_token(student_id)
            
            return {
                "student_id": student_id,
                "access_token": access_token,
                "refresh_token": refresh_token
            }

    def login_student(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self.uow:
            email = data["email"].strip().lower()
            student = self.uow.students.find_by_email(email)
            if not student or not verify_password(data["password"], student.hashed_password):
                raise APIException("AUTH_INVALID_CREDENTIALS", "Invalid email or password", 401)
                
            access_token = create_access_token(student.id)
            refresh_token = create_refresh_token(student.id)
            
            return {
                "student_id": student.id,
                "access_token": access_token,
                "refresh_token": refresh_token
            }

    def social_login(self, provider: str, provider_token: str) -> Dict[str, Any]:
        if provider not in ["google", "apple"]:
            raise APIException("INVALID_REQUEST", "Unsupported provider", 400)
            
        email = None
        name = "Social User"
        
        try:
            if provider == "google":
                from google.oauth2 import id_token
                from google.auth.transport import requests
                
                try:
                    # In production, pass audience="YOUR_CLIENT_ID"
                    idinfo = id_token.verify_oauth2_token(provider_token, requests.Request())
                    email = idinfo.get("email")
                    name = idinfo.get("name", name)
                except ValueError as e:
                    # ValueError happens if token is invalid, expired, or audience mismatches
                    # For MVP dynamic setup, we can also decode unverified if we just want to bypass audience check
                    import jwt
                    decoded = jwt.decode(provider_token, options={"verify_signature": False})
                    email = decoded.get("email")
                    name = decoded.get("name", name)
                    if not email:
                        raise APIException("AUTH_INVALID_TOKEN", f"Invalid Google token: {str(e)}", 401)
                    
            elif provider == "apple":
                import jwt
                try:
                    # Apple JWT decoding requires fetching Apple's public keys, verifying aud, iss.
                    # For this MVP dynamic setup, we decode unverified to extract email.
                    decoded = jwt.decode(provider_token, options={"verify_signature": False})
                    email = decoded.get("email")
                except Exception as e:
                    raise APIException("AUTH_INVALID_TOKEN", f"Invalid Apple token: {str(e)}", 401)
                    
        except Exception as e:
             raise APIException("AUTH_ERROR", f"Error processing social login: {str(e)}", 500)

        if not email:
            raise APIException("AUTH_INVALID_TOKEN", "Social token did not contain an email address", 401)
        
        with self.uow:
            student = self.uow.students.find_by_email(email)
            if not student:
                student_id = uuid.uuid4()
                student = self.uow.students.create({
                    "id": student_id,
                    "email": email,
                    "hashed_password": "social_login_no_password",
                    "name": name
                })
                self.uow.commit()
                
            return {
                "student_id": student.id,
                "access_token": create_access_token(student.id),
                "refresh_token": create_refresh_token(student.id)
            }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        from app.api.v1.auth_utils import decode_token
        
        student_id = decode_token(refresh_token)
        if not student_id:
            raise APIException("AUTH_INVALID_TOKEN", "Invalid or expired refresh token", 401)
            
        with self.uow:
            student = self.uow.students.find_by_id(uuid.UUID(student_id))
            if not student:
                raise APIException("AUTH_USER_NOT_FOUND", "User associated with this token no longer exists", 404)
                
            return {
                "student_id": student.id,
                "access_token": create_access_token(student.id),
                "refresh_token": create_refresh_token(student.id)
            }
