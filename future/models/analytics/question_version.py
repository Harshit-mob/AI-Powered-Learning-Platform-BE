import uuid
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class QuestionVersion(Base):
    __tablename__ = "question_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    
    version = Column(Integer, nullable=False)
    created_from = Column(UUID(as_uuid=True), ForeignKey("question_versions.id"), nullable=True)
    change_reason = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    question = relationship("Question")
