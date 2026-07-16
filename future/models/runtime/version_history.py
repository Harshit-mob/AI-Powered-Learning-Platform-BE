import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.session import Base

class QuestionVersionHistory(Base):
    __tablename__ = "question_version_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    new_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    
    version_number = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    validator_source = Column(String, nullable=True)
    generator_version = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
