import uuid
from sqlalchemy import Column, Float, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class QuestionAnalytics(Base):
    __tablename__ = "question_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, unique=True)
    
    total_attempts = Column(Integer, nullable=False, default=0)
    accuracy_rate = Column(Float, nullable=False, default=0.0)
    skip_rate = Column(Float, nullable=False, default=0.0)
    
    avg_thinking_time = Column(Float, nullable=False, default=0.0)
    avg_speaking_time = Column(Float, nullable=False, default=0.0)
    wrong_option_distribution = Column(JSONB, nullable=True)
    
    difficulty_index = Column(Float, nullable=False, default=0.0)
    discrimination_index = Column(Float, nullable=False, default=0.0)
    retirement_score = Column(Float, nullable=False, default=0.0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    question = relationship("Question")

class LearningUnitAnalytics(Base):
    __tablename__ = "learning_unit_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_unit_id = Column(UUID(as_uuid=True), ForeignKey("learning_units.id"), nullable=False, unique=True)
    
    total_attempts = Column(Integer, nullable=False, default=0)
    average_mastery = Column(Float, nullable=False, default=0.0)
    common_misconceptions = Column(JSONB, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
