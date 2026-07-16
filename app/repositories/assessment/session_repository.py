from typing import Optional, List, Any, Dict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.models.assessment.learning_session import LearningSession
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException

class SessionRepository(BaseRepository[LearningSession]):
    def __init__(self, session):
        super().__init__(LearningSession, session)

    def create_session(self, session_data: Dict[str, Any]) -> LearningSession:
        return self.create(session_data)

    def finish_session(self, session_id: uuid.UUID, finish_data: Dict[str, Any]) -> Optional[LearningSession]:
        return self.update(session_id, finish_data)

    def active_session(self, student_id: uuid.UUID) -> Optional[LearningSession]:
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id,
                self.model.end_time.is_(None)
            ).order_by(self.model.start_time.desc()).limit(1)
            return self.session.scalars(stmt).first()
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting active session: {str(e)}")

    def student_sessions(self, student_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[LearningSession]:
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id
            ).order_by(self.model.start_time.desc()).offset(skip).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting student sessions: {str(e)}")

    def recent_sessions(self, limit: int = 20) -> List[LearningSession]:
        try:
            stmt = select(self.model).order_by(self.model.start_time.desc()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting recent sessions: {str(e)}")
