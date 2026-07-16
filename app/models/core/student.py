import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grade_id = Column(UUID(as_uuid=True), nullable=True) # Assuming references external grade table
    board_id = Column(UUID(as_uuid=True), nullable=True) # Assuming references external board table
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    
    streak_days = Column(Integer, nullable=False, default=0)
    total_study_minutes = Column(Integer, nullable=False, default=0)
    
    total_xp = Column(Integer, nullable=False, default=0)
    current_level = Column(Integer, nullable=False, default=1)
    
    overall_mastery_percentage = Column(Float, nullable=False, default=0.0)
    overall_confidence_score = Column(Float, nullable=False, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    mastery_records = relationship("StudentMastery", back_populates="student", cascade="all, delete-orphan")
    sessions = relationship("LearningSession", back_populates="student", cascade="all, delete-orphan")
