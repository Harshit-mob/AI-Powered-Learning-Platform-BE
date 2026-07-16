import uuid
from sqlalchemy import Column, Float, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class StudentResponse(Base):
    __tablename__ = "student_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("learning_sessions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    
    provided_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    time_taken_seconds = Column(Float, nullable=False)
    voice_score = Column(Float, nullable=True)
    hints_used = Column(Integer, nullable=False, default=0)
    confidence_rating = Column(Float, nullable=True)
    attempt_number = Column(Integer, nullable=False, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("LearningSession", back_populates="responses")
    question = relationship("Question")
