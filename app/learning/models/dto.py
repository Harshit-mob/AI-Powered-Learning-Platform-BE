from pydantic import BaseModel
from typing import List, Dict, Any
import uuid

class MasteryUpdatePayload(BaseModel):
    concept_id: uuid.UUID
    old_mastery: float
    new_mastery: float
    old_status: str
    new_status: str
    confidence_score: float

class ReviewUpdatePayload(BaseModel):
    concept_id: uuid.UUID
    next_review: str # ISO Date
    interval: float
    ease_factor: float

class LearningEventPayload(BaseModel):
    event_name: str
    entity_type: str
    entity_id: str
    payload: Dict[str, Any]

class LearningOutcome(BaseModel):
    session_id: uuid.UUID
    student_id: uuid.UUID
    mastery_updates: List[MasteryUpdatePayload]
    review_updates: List[ReviewUpdatePayload]
    generated_events: List[LearningEventPayload]
    progress_summary: Dict[str, Any]

    class Config:
        frozen = True
