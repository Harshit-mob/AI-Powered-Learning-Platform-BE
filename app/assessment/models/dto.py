from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
from app.constants.session import SessionType
from app.constants.difficulty import QuestionDifficulty

class QuestionPayload(BaseModel):
    id: uuid.UUID
    learning_unit_id: uuid.UUID
    question_text: str
    question_type: str
    difficulty: QuestionDifficulty
    bloom_level: str
    cognitive_level: str
    options: Optional[List[Dict[str, Any]]] = None
    hints: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class GeneratedSession(BaseModel):
    session_id: uuid.UUID
    session_type: SessionType
    student_id: uuid.UUID
    content_id: uuid.UUID
    estimated_minutes: int
    question_count: int
    questions: List[QuestionPayload]
    metadata: Dict[str, Any]

    class Config:
        frozen = True # Immutable DTO

class AnswerSubmission(BaseModel):
    session_id: uuid.UUID
    question_id: uuid.UUID
    student_id: uuid.UUID
    provided_answer: Any
    time_taken_seconds: float
    hints_used: int
    device_type: str
    voice_transcript: Optional[str] = None
    confidence_rating: Optional[float] = None

class EvaluationResult(BaseModel):
    session_id: uuid.UUID
    question_id: uuid.UUID
    student_id: uuid.UUID
    is_correct: bool
    evaluation_score: float
    evaluation_method: str
    matched_answer: str
    voice_score: Optional[float] = None
    response_time: float
    hints_used: int
    
    class Config:
        frozen = True
