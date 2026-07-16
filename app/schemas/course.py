from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional

# --- Subtopic Schemas ---
class SubtopicBase(BaseModel):
    title: str
    content: str

class SubtopicCreate(SubtopicBase):
    topic_id: UUID

class SubtopicResponse(SubtopicBase):
    id: UUID
    topic_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True) # Allows reading from SQLAlchemy models

# --- Topic Schemas ---
class TopicBase(BaseModel):
    title: str

class TopicCreate(TopicBase):
    chapter_id: UUID

class TopicResponse(TopicBase):
    id: UUID
    chapter_id: UUID
    subtopics: List[SubtopicResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Chapter Schemas ---
class ChapterBase(BaseModel):
    title: str
    description: Optional[str] = None

class ChapterCreate(ChapterBase):
    pass

class ChapterResponse(ChapterBase):
    id: UUID
    topics: List[TopicResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
