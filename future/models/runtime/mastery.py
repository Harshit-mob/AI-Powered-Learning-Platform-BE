import uuid
import enum
from sqlalchemy import Column, Float, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class MasteryStatus(str, enum.Enum):
    NEW = "NEW"
    LEARNING = "LEARNING"
    PRACTICING = "PRACTICING"
    MASTERED = "MASTERED"
    REVIEW = "REVIEW"

class StudentMastery(Base):
    __tablename__ = "student_mastery"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    learning_unit_id = Column(UUID(as_uuid=True), ForeignKey("learning_units.id"), nullable=False)
    
    mastery_percentage = Column(Float, nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=False, default=0.0)
    
    correct_count = Column(Integer, nullable=False, default=0)
    wrong_count = Column(Integer, nullable=False, default=0)
    avg_thinking_time = Column(Float, nullable=False, default=0.0)
    avg_speaking_time = Column(Float, nullable=False, default=0.0)
    
    last_practiced = Column(DateTime(timezone=True), nullable=True)
    next_review = Column(DateTime(timezone=True), nullable=True)
    review_interval_days = Column(Float, nullable=False, default=1.0)
    forgetting_score = Column(Float, nullable=False, default=0.0)
    ease_factor = Column(Float, nullable=False, default=2.5)
    
    status = Column(Enum(MasteryStatus, name="mastery_status_enum", create_type=True), nullable=False, default=MasteryStatus.NEW)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="mastery_records")
    learning_unit = relationship("LearningUnit")
