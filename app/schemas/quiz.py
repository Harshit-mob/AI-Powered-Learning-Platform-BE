from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

# --- Question Schemas ---
class QuestionBase(BaseModel):
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str = Field(..., max_length=1)

class QuestionCreate(QuestionBase):
    subtopic_id: UUID

class QuestionResponse(QuestionBase):
    id: UUID
    subtopic_id: UUID
    created_at: datetime
    
    # We return the correct option here for testing, but in production
    # you might want to hide it in the response model.
    model_config = ConfigDict(from_attributes=True)


# --- Quiz Session Schemas ---
class QuizSessionCreate(BaseModel):
    # Empty for now, used to start a session
    pass

class QuizSessionResponse(BaseModel):
    id: UUID
    score: int
    start_time: datetime
    end_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Answer Submission Schemas ---
class AnswerSubmit(BaseModel):
    session_id: UUID
    question_id: UUID
    selected_option: str = Field(..., max_length=1)

class AnswerResponse(BaseModel):
    id: UUID
    session_id: UUID
    question_id: UUID
    selected_option: str
    is_correct: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
