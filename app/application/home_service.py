import uuid
from typing import Dict, Any
from app.repositories.base.unit_of_work import UnitOfWork

class HomeService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_home_dashboard(self, student_id: uuid.UUID) -> Dict[str, Any]:
        with self.uow:
            # Here we would query the student's active chapter, today's schedule, and goals.
            return {
                "today": {
                    "daily_practice": {
                        "available": True,
                        "completed": False,
                        "duration": 10
                    },
                    "chapter_revision": {
                        "available": True,
                        "completed": False,
                        "duration": 15
                    },
                    "streak": 12,
                    "goal_progress": 60
                }
            }
