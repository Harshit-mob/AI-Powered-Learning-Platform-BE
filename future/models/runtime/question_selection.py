import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.session import Base

class QuestionSelectionLog(Base):
    __tablename__ = "question_selection_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("learning_sessions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    
    selection_reason = Column(String, nullable=False)
    expected_difficulty = Column(String, nullable=True)
    confidence_at_selection = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
