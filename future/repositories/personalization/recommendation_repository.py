from typing import List, Any, Dict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.models.personalization.recommendation_history import RecommendationHistory
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException
from app.constants.recommendation import CompletionStatus

class RecommendationRepository(BaseRepository[RecommendationHistory]):
    def __init__(self, session):
        super().__init__(RecommendationHistory, session)

    def create_recommendation(self, rec_data: Dict[str, Any]) -> RecommendationHistory:
        return self.create(rec_data)

    def latest_recommendations(self, student_id: uuid.UUID, limit: int = 10) -> List[RecommendationHistory]:
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id
            ).order_by(self.model.created_at.desc()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting latest recommendations: {str(e)}")

    def pending_recommendations(self, student_id: uuid.UUID, limit: int = 10) -> List[RecommendationHistory]:
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id,
                self.model.completion_status == CompletionStatus.PENDING.value
            ).order_by(self.model.created_at.desc()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting pending recommendations: {str(e)}")

    def completed_recommendations(self, student_id: uuid.UUID, limit: int = 10) -> List[RecommendationHistory]:
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id,
                self.model.completion_status == CompletionStatus.COMPLETED.value
            ).order_by(self.model.completed_at.desc()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting completed recommendations: {str(e)}")
