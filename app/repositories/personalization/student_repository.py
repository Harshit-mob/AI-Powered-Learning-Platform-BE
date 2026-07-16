from typing import Optional, List, Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.models.core.student import Student
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException

class StudentRepository(BaseRepository[Student]):
    def __init__(self, session):
        super().__init__(Student, session)

    def find_by_id(self, student_id: uuid.UUID) -> Optional[Student]:
        return self.get_by_id(student_id)

    def find_by_email(self, email: str) -> Optional[Student]:
        try:
            stmt = select(self.model).where(self.model.email == email)
            return self.session.scalars(stmt).first()
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error finding student by email: {str(e)}")

    def update_statistics(self, student_id: uuid.UUID, stats_in: Dict[str, Any]) -> Optional[Student]:
        return self.update(student_id, stats_in)

    def find_active_students(self, limit: int = 100) -> List[Student]:
        try:
            stmt = select(self.model).where(self.model.streak_days > 0).order_by(self.model.streak_days.desc()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error fetching active students: {str(e)}")
