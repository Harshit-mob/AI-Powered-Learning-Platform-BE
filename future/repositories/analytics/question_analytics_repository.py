from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.models.analytics.question_analytics import QuestionAnalytics
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException

class QuestionAnalyticsRepository(BaseRepository[QuestionAnalytics]):
    def __init__(self, session):
        super().__init__(QuestionAnalytics, session)

    def get_by_question_id(self, question_id: uuid.UUID) -> Optional[QuestionAnalytics]:
        return self.first({"question_id": question_id})

    def increment_attempt(self, question_id: uuid.UUID) -> None:
        try:
            analytics = self.get_by_question_id(question_id)
            if not analytics:
                analytics = QuestionAnalytics(question_id=question_id, total_attempts=1)
                self.session.add(analytics)
            else:
                analytics.total_attempts += 1
            self.session.flush()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Error incrementing attempt: {str(e)}")

    def update_accuracy(self, question_id: uuid.UUID, new_accuracy: float) -> None:
        self._update_field(question_id, "accuracy_rate", new_accuracy)

    def update_skip_rate(self, question_id: uuid.UUID, new_skip_rate: float) -> None:
        self._update_field(question_id, "skip_rate", new_skip_rate)

    def update_response_time(self, question_id: uuid.UUID, avg_response_time: float) -> None:
        self._update_field(question_id, "average_response_time", avg_response_time)

    def update_voice_score(self, question_id: uuid.UUID, avg_voice_score: float) -> None:
        self._update_field(question_id, "average_voice_score", avg_voice_score)

    def _update_field(self, question_id: uuid.UUID, field: str, value: float) -> None:
        try:
            analytics = self.get_by_question_id(question_id)
            if not analytics:
                analytics = QuestionAnalytics(question_id=question_id)
                setattr(analytics, field, value)
                self.session.add(analytics)
            else:
                setattr(analytics, field, value)
            self.session.flush()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Error updating {field}: {str(e)}")
