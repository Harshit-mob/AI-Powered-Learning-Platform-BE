import uuid
from typing import List, Optional
from pydantic import BaseModel
from app.runtime.session.session_types import SessionType, SessionState, LearningContext

class QuestionDTO(BaseModel):
    question_id: uuid.UUID
    question_type: str
    difficulty: str
    question: str
    options: List[str]
    hint_1: Optional[str]
    hint_2: Optional[str]
    supported_answer_modes: List[str]

class SessionPayload(BaseModel):
    session_id: uuid.UUID
    questions: List[QuestionDTO]
    
    class Config:
        frozen = True
