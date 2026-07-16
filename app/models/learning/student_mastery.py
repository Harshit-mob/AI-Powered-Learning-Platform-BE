import uuid
from sqlalchemy import Column, Float, DateTime, ForeignKey, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class StudentMastery(Base):
    __tablename__ = "student_mastery"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    # In Phase 1, we map learning_unit_id into this column
    concept_id = Column(UUID(as_uuid=True), nullable=False)
    learning_objective_id = Column(UUID(as_uuid=True), nullable=True) # Optional FK depending on schema
    
    mastery_percentage = Column(Float, nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=False, default=0.0)
    
    correct_count = Column(Integer, nullable=False, default=0)
    wrong_count = Column(Integer, nullable=False, default=0)
    
    last_practiced = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default="NEW") # NEW, LEARNING, PRACTICING, MASTERED, REVIEW

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_student_mastery_student_concept", "student_id", "concept_id", unique=True),
        Index("ix_student_mastery_student_lo", "student_id", "learning_objective_id", unique=True)
    )

    student = relationship("Student", back_populates="mastery_records")
