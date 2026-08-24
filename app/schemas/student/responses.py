from pydantic import BaseModel
from typing import List, Optional
import uuid

class StudentProfileResponse(BaseModel):
    name: str
    email: str
    current_streak: int
    current_level: int
    total_xp: int
    target_xp: int
    daily_goal_minutes: int
    total_mastery_percentage: int
    completed_sessions: int
    role: str

class RecentSessionDTO(BaseModel):
    session_id: str
    date: Optional[str]
    score: int

class ChapterProgressDTO(BaseModel):
    chapter_id: str
    chapter_title: str
    progress: int

class SubjectProgressDTO(BaseModel):
    subject_id: str
    subject_name: str
    progress: int
    chapters: List[ChapterProgressDTO]

class StudentProgressResponse(BaseModel):
    overall_progress: int
    current_level: int
    total_xp: int
    target_xp: int
    streak_days: int
    subject_progress: List[SubjectProgressDTO]
    current_mastery: int
    recent_sessions: List[RecentSessionDTO]

class DailyCheckinStatusResponse(BaseModel):
    is_completed: bool
    learning_date: str

class WeeklyStreakDayResponse(BaseModel):
    day_name: str
    date: str
    full_date: str
    completed: bool
    is_today: bool
