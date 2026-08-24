from pydantic import BaseModel

class HomeTaskDTO(BaseModel):
    available: bool
    completed: bool
    duration: int

class HomeTodayDTO(BaseModel):
    daily_practice: HomeTaskDTO
    chapter_revision: HomeTaskDTO
    streak: int
    goal_progress: int

class HomeDashboardResponse(BaseModel):
    today: HomeTodayDTO
