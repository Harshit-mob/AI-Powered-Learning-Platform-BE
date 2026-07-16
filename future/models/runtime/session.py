import uuid
from sqlalchemy import Column, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id"), nullable=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    accuracy = Column(Float, nullable=False, default=0.0)
    mastery_gain = Column(Float, nullable=False, default=0.0)
    
    weak_concepts = Column(JSONB, nullable=True)
    strong_concepts = Column(JSONB, nullable=True)
    
    avg_thinking_speed = Column(Float, nullable=False, default=0.0)
    avg_voice_performance = Column(Float, nullable=False, default=0.0)
    session_confidence = Column(Float, nullable=False, default=0.0)
    
    recommendation = Column(Text, nullable=True)

    student = relationship("Student", back_populates="sessions")
    responses = relationship("StudentResponse", back_populates="session", cascade="all, delete-orphan")
