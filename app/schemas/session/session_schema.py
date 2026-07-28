from pydantic import Field
from typing import List, Optional
import uuid
from app.schemas.common.base import CamelBaseModel

class SessionGenerateRequest(CamelBaseModel):
    scope: str = Field(..., description="Must be TOPIC, CHAPTER, MULTI_TOPIC, or STUDENT")
    ids: List[uuid.UUID] = Field(..., min_length=1)
    session_type: Optional[str] = Field(default=None, description="Optional session type, e.g. DAILY_PRACTICE, REVISION")

    model_config = {
        "json_schema_extra": {
            "example": {
                "scope": "MULTI_TOPIC",
                "ids": ["7868a3f7-d314-44ba-bbc4-3eb88a2fa419", "0ec69a28-0f7d-4fe0-b78b-68c62f5c952c"],
                "sessionType": "REVISION"
            }
        }
    }

class AnswerSubmissionRequest(CamelBaseModel):
    session_id: uuid.UUID
    question_id: uuid.UUID
    student_answer: str
    time_taken: int
    hints_used: int = Field(default=0, description="Number of hints the student used")
    device_type: str = Field(default="UNKNOWN", description="The client device type (e.g. IOS, ANDROID, WEB)")
    answer_mode: str = Field(..., description="Must be VOICE, TEXT, or MCQ")
    is_skipped: Optional[bool] = Field(default=False, description="Set to true if the student skipped the question")
