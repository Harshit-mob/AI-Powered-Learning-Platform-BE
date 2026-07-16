import uuid
from sqlalchemy import Column, Float, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class StudentReviewSchedule(Base):
    __tablename__ = "student_review_schedule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=False)
    
    scheduler_type = Column(String, nullable=False, default="SM2") # SM2, FSRS
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review = Column(DateTime(timezone=True), nullable=True, index=True)
    
    review_count = Column(Integer, nullable=False, default=0)
    successive_correct_reviews = Column(Integer, nullable=False, default=0)
    
    scheduler_metadata = Column(JSONB, nullable=True)
    
    interval = Column(Float, nullable=False, default=0.0)
    ease_factor = Column(Float, nullable=False, default=2.5)
    stability = Column(Float, nullable=False, default=0.0)
    difficulty = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="review_schedules")
    concept = relationship("Concept")
