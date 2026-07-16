import uuid
from sqlalchemy import Column, Float, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    
    content_type = Column(String, nullable=False) # BOOK, CHAPTER, TOPIC, SUBTOPIC, LEARNING_UNIT, MIXED
    content_id = Column(UUID(as_uuid=True), nullable=False)
    
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    session_duration_seconds = Column(Integer, nullable=False, default=0)
    questions_requested = Column(Integer, nullable=False, default=0)
    questions_answered = Column(Integer, nullable=False, default=0)
    questions_correct = Column(Integer, nullable=False, default=0)
    questions_skipped = Column(Integer, nullable=False, default=0)
    
    average_response_time = Column(Float, nullable=False, default=0.0)
    average_voice_score = Column(Float, nullable=False, default=0.0)
    
    completion_reason = Column(String, nullable=True) # COMPLETED, TIMEOUT, STUDENT_EXITED, TEACHER_ENDED
    
    accuracy = Column(Float, nullable=False, default=0.0)
    mastery_gain = Column(Float, nullable=False, default=0.0)
    
    weak_concepts = Column(JSONB, nullable=True)
    strong_concepts = Column(JSONB, nullable=True)
    
    session_type = Column(String, nullable=False) # PRACTICE, REVISION, ASSESSMENT, RECOVERY, CHALLENGE, etc.

    student = relationship("Student", back_populates="sessions")
    responses = relationship("StudentResponse", back_populates="session", cascade="all, delete-orphan")
