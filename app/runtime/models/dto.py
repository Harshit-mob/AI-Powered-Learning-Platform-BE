from pydantic import BaseModel
from typing import List, Dict, Any
import uuid

class RecommendationItem(BaseModel):
    id: uuid.UUID
    priority: int
    reason: str
    target_content_id: uuid.UUID
    target_content_type: str
    recommended_session_type: str

class NextSessionInfo(BaseModel):
    session_type: str
    reason: str
    target_content_ids: List[uuid.UUID]

class GoalProgressInfo(BaseModel):
    study_minutes_today: int
    questions_answered_today: int
    concepts_mastered_today: int
    daily_streak: int
    weekly_streak: int
    goal_completed: bool

class PersonalizationOutcome(BaseModel):
    student_id: uuid.UUID
    session_id: uuid.UUID
    recommendations: List[RecommendationItem]
    next_session: NextSessionInfo
    learning_path: List[str] # List of steps, e.g. ["REVISION", "PRACTICE", "ASSESSMENT"]
    goal_progress: GoalProgressInfo
    preference_adjustments: Dict[str, Any]

    class Config:
        frozen = True
