from typing import Optional, List, Any, Dict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import uuid

from app.models.learning.student_review_schedule import StudentReviewSchedule
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException

class ReviewScheduleRepository(BaseRepository[StudentReviewSchedule]):
    def __init__(self, session):
        super().__init__(StudentReviewSchedule, session)

    def due_reviews(self, student_id: uuid.UUID, as_of: datetime, limit: int = 50) -> List[StudentReviewSchedule]:
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id,
                self.model.next_review <= as_of
            ).order_by(self.model.next_review.asc()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting due reviews: {str(e)}")

    def overdue_reviews(self, student_id: uuid.UUID, as_of: datetime, limit: int = 50) -> List[StudentReviewSchedule]:
        # Semantically overdue could mean past a certain tolerance, but practically it's the same logic, maybe ordered strictly by how old.
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id,
                self.model.next_review < as_of
            ).order_by(self.model.next_review.asc()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting overdue reviews: {str(e)}")

    def update_schedule(self, schedule_id: uuid.UUID, schedule_data: Dict[str, Any]) -> Optional[StudentReviewSchedule]:
        return self.update(schedule_id, schedule_data)

    def create_schedule(self, schedule_data: Dict[str, Any]) -> StudentReviewSchedule:
        return self.create(schedule_data)

    def delete_schedule(self, schedule_id: uuid.UUID) -> bool:
        return self.delete(schedule_id)
