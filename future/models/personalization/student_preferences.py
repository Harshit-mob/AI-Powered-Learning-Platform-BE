import uuid
from sqlalchemy import Column, String, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base

class StudentPreferences(Base):
    __tablename__ = "student_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    language = Column(String, nullable=False, default="English")
    voice_enabled = Column(Boolean, nullable=False, default=False)
    difficulty_preference = Column(String, nullable=False, default="STANDARD")
    daily_goal = Column(Integer, nullable=False, default=30)
    
    notification_time = Column(String, nullable=True)
    preferred_scheduler = Column(String, nullable=False, default="SM2")
    theme = Column(String, nullable=False, default="LIGHT")
    parent_mode = Column(Boolean, nullable=False, default=False)

    student = relationship("Student", back_populates="preferences")
