from typing import Optional, List, Any, Dict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.models.learning.student_mastery import StudentMastery
from app.repositories.base.base_repository import BaseRepository
from app.repositories.exceptions import RepositoryException
from app.constants.mastery import MasteryStatus

class MasteryRepository(BaseRepository[StudentMastery]):
    def __init__(self, session):
        super().__init__(StudentMastery, session)

    def get_by_student(self, student_id: uuid.UUID) -> List[StudentMastery]:
        return self.filter({"student_id": student_id})

    def get_by_concept(self, student_id: uuid.UUID, concept_id: uuid.UUID) -> Optional[StudentMastery]:
        return self.first({"student_id": student_id, "concept_id": concept_id})

    def upsert_mastery(self, student_id: uuid.UUID, concept_id: uuid.UUID, mastery_data: Dict[str, Any]) -> StudentMastery:
        try:
            mastery = self.get_by_concept(student_id, concept_id)
            if mastery:
                for key, value in mastery_data.items():
                    setattr(mastery, key, value)
            else:
                mastery = StudentMastery(student_id=student_id, concept_id=concept_id, **mastery_data)
                self.session.add(mastery)
            self.session.flush()
            return mastery
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryException(f"Error upserting mastery: {str(e)}")

    def update_mastery(self, mastery_id: uuid.UUID, update_data: Dict[str, Any]) -> Optional[StudentMastery]:
        return self.update(mastery_id, update_data)

    def get_low_mastery(self, student_id: uuid.UUID, threshold: float = 0.4, limit: int = 20) -> List[StudentMastery]:
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id,
                self.model.mastery_percentage < threshold
            ).order_by(self.model.mastery_percentage.asc()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting low mastery: {str(e)}")

    def get_mastered(self, student_id: uuid.UUID, threshold: float = 0.85, limit: int = 50) -> List[StudentMastery]:
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id,
                self.model.mastery_percentage >= threshold
            ).order_by(self.model.mastery_percentage.desc()).limit(limit)
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting mastered concepts: {str(e)}")

    def get_review_candidates(self, student_id: uuid.UUID) -> List[StudentMastery]:
        try:
            stmt = select(self.model).where(
                self.model.student_id == student_id,
                self.model.status == MasteryStatus.REVIEW.value
            )
            return list(self.session.scalars(stmt).all())
        except SQLAlchemyError as e:
            raise RepositoryException(f"Error getting review candidates: {str(e)}")
