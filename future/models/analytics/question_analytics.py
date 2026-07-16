import uuid
from sqlalchemy import Column, Float, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class QuestionAnalytics(Base):
    __tablename__ = "question_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    total_attempts = Column(Integer, nullable=False, default=0)
    accuracy_rate = Column(Float, nullable=False, default=0.0)
    skip_rate = Column(Float, nullable=False, default=0.0)
    
    difficulty_index = Column(Float, nullable=False, default=0.0)
    discrimination_index = Column(Float, nullable=False, default=0.0)
    retirement_score = Column(Float, nullable=False, default=0.0)
    
    average_response_time = Column(Float, nullable=False, default=0.0)
    average_hint_usage = Column(Float, nullable=False, default=0.0)
    average_voice_score = Column(Float, nullable=False, default=0.0)
    
    rolling_30_day_accuracy = Column(Float, nullable=False, default=0.0)
    rolling_90_day_accuracy = Column(Float, nullable=False, default=0.0)

    last_attempted = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    question = relationship("Question")
