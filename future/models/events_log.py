import uuid
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.database.session import Base

class EventsLog(Base):
    __tablename__ = "events_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False, index=True)
    
    version = Column(Integer, nullable=False, default=1)
    correlation_id = Column(String, nullable=True, index=True)
    causation_id = Column(String, nullable=True)
    
    payload = Column(JSONB, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True) # trace_id, request_id, user_agent, ip, platform
    
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_by = Column(String, nullable=True)
