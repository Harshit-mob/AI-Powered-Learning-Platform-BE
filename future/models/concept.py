import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_unit_id = Column(UUID(as_uuid=True), ForeignKey("learning_units.id"), nullable=False)
    
    normalized_name = Column(String, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    learning_unit = relationship("LearningUnit")
