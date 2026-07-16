import uuid
from sqlalchemy import Column, String, Date, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class StudentDailyLearning(Base):
    __tablename__ = "student_daily_learning"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    
    learning_date = Column(Date, nullable=False)
    source = Column(String, nullable=False, default="SCHOOL")
    status = Column(String, nullable=False, default="PENDING") # PENDING, COMPLETED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    student = relationship("Student")
    topic = relationship("Topic")
