from pydantic import Field, BaseModel
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

class XpBreakdown(BaseModel):
    xp_from_correct: int
    completion_bonus: int
    accuracy_bonus: int
    total: int

class DailyGoalProgress(BaseModel):
    completed: bool
    streak_maintained: bool

class SessionResult(BaseModel):
    corrected: int
    wrong: int
    skipped: int

class SessionCompleteResponse(BaseModel):
    score: int
    xp_breakdown: XpBreakdown
    accuracy: float
    mastery_gain: float
    total_xp: int
    current_level: int
    leveled_up: bool
    weak_learning_units: List[str]
    strong_learning_units: List[str]
    recommended_next_session: str
    daily_goal_progress: DailyGoalProgress
    streak: int
    session_summary: str
    result: SessionResult
    total_time_taken: float

class QuestionDTOResponse(BaseModel):
    question_id: uuid.UUID
    question_type: str
    difficulty: str
    question: str
    options: List[str]
    hint_1: Optional[str]
    hint_2: Optional[str]
    supported_answer_modes: List[str]

class SessionGenerateResponse(BaseModel):
    session_id: uuid.UUID
    questions: List[QuestionDTOResponse]

class AnswerResponse(BaseModel):
    status: str
    evaluation: float
    correct_answer: str
    explanation: str
    mastery_change: float

class RecommendationCard(BaseModel):
    title: str
    priority: int
    estimated_duration: int
    question_count: int
    xp_reward: int
    status: str
    reason: str
    session_type: str
    content_type: str
    content_ids: List[uuid.UUID]
