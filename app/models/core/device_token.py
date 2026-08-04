import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base


class StudentDeviceToken(Base):
    __tablename__ = "student_device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    token = Column(String, nullable=False)
    platform = Column(String, nullable=False)   # "android" | "ios"
    device_id = Column(String, nullable=True)   # optional unique device identifier from mobile

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="device_tokens")

    __table_args__ = (
        # One row per student+device combination
        UniqueConstraint("student_id", "device_id", name="uq_student_device"),
    )
