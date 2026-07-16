import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="SET NULL"), nullable=True)
    
    recommendation_source = Column(String, nullable=False) # MASTERY_ENGINE, TEACHER, ADAPTIVE_ENGINE
    recommendation_reason = Column(String, nullable=False)
    recommendation_priority = Column(String, nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    
    target_learning_unit_id = Column(UUID(as_uuid=True), nullable=True)
    
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_status = Column(String, nullable=False, default="PENDING") # PENDING, ACCEPTED, COMPLETED, IGNORED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="recommendations")
