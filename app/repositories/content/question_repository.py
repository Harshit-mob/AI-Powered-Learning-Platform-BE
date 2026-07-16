from typing import List
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.models.quiz import Question
from app.models.course import LearningUnit, Subtopic, Topic
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException

class QuestionRepository(BaseRepository[Question]):
    def __init__(self, session):
        super().__init__(Question, session)

    def find_by_learning_unit(self, learning_unit_id: uuid.UUID, limit: int = 50) -> List[Question]:
        try:
            stmt = select(self.model).where(
                self.model.learning_unit_id == learning_unit_id
            ).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error finding questions by learning unit: {str(e)}")

    def find_by_topic_id(self, topic_id: uuid.UUID, limit: int = 500) -> List[Question]:
        try:
            stmt = select(self.model).join(LearningUnit).join(Subtopic).where(
                Subtopic.topic_id == topic_id
            ).options(joinedload(self.model.learning_unit)).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error finding questions by topic: {str(e)}")

    def find_by_chapter_id(self, chapter_id: uuid.UUID, limit: int = 500) -> List[Question]:
        try:
            stmt = select(self.model).join(LearningUnit).join(Subtopic).join(Topic).where(
                Topic.chapter_id == chapter_id
            ).options(joinedload(self.model.learning_unit)).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error finding questions by chapter: {str(e)}")

    def find_by_concept(self, concept_id: uuid.UUID, limit: int = 50) -> List[Question]:
        # Assuming concepts map to questions in a specific way in the knowledge graph
        # For now, placeholder or joining via concepts if relation exists
        return []

    def find_by_difficulty(self, difficulty: str, limit: int = 50) -> List[Question]:
        try:
            stmt = select(self.model).where(
                self.model.difficulty_level == difficulty
            ).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error finding questions by difficulty: {str(e)}")

    def find_by_question_ids(self, question_ids: List[uuid.UUID]) -> List[Question]:
        try:
            stmt = select(self.model).where(
                self.model.id.in_(question_ids)
            )
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error finding questions by ids: {str(e)}")

    def random_candidates(self, learning_unit_id: uuid.UUID, limit: int = 10) -> List[Question]:
        try:
            stmt = select(self.model).where(
                self.model.learning_unit_id == learning_unit_id
            ).order_by(func.random()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting random candidates: {str(e)}")
