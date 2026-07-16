from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid

class QuestionQualityReport(BaseModel):
    question_id: uuid.UUID
    flagged: bool
    reason: str
    metrics: Dict[str, Any]

class StudentAnalyticsReport(BaseModel):
    student_id: uuid.UUID
    total_study_minutes: int
    learning_velocity: float
    concepts_mastered: int
    weak_concepts: List[uuid.UUID]
    strong_concepts: List[uuid.UUID]
    
class TeacherDashboardReport(BaseModel):
    class_id: uuid.UUID
    average_mastery: float
    weakest_concepts: List[uuid.UUID]
    strongest_concepts: List[uuid.UUID]
    flagged_questions: List[uuid.UUID]
    average_accuracy: float
