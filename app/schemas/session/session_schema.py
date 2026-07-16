from pydantic import Field
from typing import List, Optional
import uuid
from app.schemas.common.base import CamelBaseModel

class SessionGenerateRequest(CamelBaseModel):
    scope: str = Field(..., description="Must be TOPIC, CHAPTER, MULTI_TOPIC, or STUDENT")
    ids: List[uuid.UUID] = Field(..., min_length=1)

class AnswerSubmissionRequest(CamelBaseModel):
    session_id: uuid.UUID
    question_id: uuid.UUID
    student_answer: str
    time_taken: int
    hints_used: int = Field(default=0, description="Number of hints the student used")
    device_type: str = Field(default="UNKNOWN", description="The client device type (e.g. IOS, ANDROID, WEB)")
    answer_mode: str = Field(..., description="Must be VOICE, TEXT, or MCQ")
    is_skipped: Optional[bool] = Field(default=False, description="Set to true if the student skipped the question")
