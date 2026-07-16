from typing import Optional, List, Any, Dict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.models.assessment.student_response import StudentResponse
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException

class ResponseRepository(BaseRepository[StudentResponse]):
    def __init__(self, session):
        super().__init__(StudentResponse, session)

    def save_response(self, response_data: Dict[str, Any]) -> StudentResponse:
        return self.create(response_data)

    def session_responses(self, session_id: uuid.UUID) -> List[StudentResponse]:
        try:
            stmt = select(self.model).where(
                self.model.session_id == session_id
            ).order_by(self.model.created_at.asc())
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting session responses: {str(e)}")

    def question_attempts(self, student_id: uuid.UUID, question_id: uuid.UUID) -> List[StudentResponse]:
        try:
            stmt = select(self.model).join(self.model.session).where(
                self.model.session.has(student_id=student_id),
                self.model.question_id == question_id
            ).order_by(self.model.created_at.asc())
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting question attempts: {str(e)}")

    def student_attempts(self, student_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
        try:
            stmt = select(self.model).join(self.model.session).where(
                self.model.session.has(student_id=student_id)
            ).order_by(self.model.created_at.desc()).offset(skip).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting student attempts: {str(e)}")

    def latest_attempt(self, student_id: uuid.UUID, question_id: uuid.UUID) -> Optional[StudentResponse]:
        try:
            stmt = select(self.model).join(self.model.session).where(
                self.model.session.has(student_id=student_id),
                self.model.question_id == question_id
            ).order_by(self.model.created_at.desc()).limit(1)
            return self.session.scalars(stmt).first()
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting latest attempt: {str(e)}")
