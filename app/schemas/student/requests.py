from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import date

class DailyCheckinRequest(BaseModel):
    learning_date: date
    topic_ids: List[uuid.UUID]
    source: str = Field(default="SCHOOL")
