import uuid
from typing import List, Dict, Any
from app.repositories.base.unit_of_work import UnitOfWork

from app.application.recommendations.providers.daily_practice import DailyPracticeProvider
from app.application.recommendations.providers.weak_point import WeakPointProvider
from app.application.recommendations.providers.revision import RevisionProvider

class RecommendationEngine:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.providers = [
            DailyPracticeProvider(self.uow),
            RevisionProvider(self.uow),
            WeakPointProvider(self.uow)
        ]

    def get_recommendations(self, student_id: uuid.UUID) -> List[Dict[str, Any]]:
        recommendations = []
        
        with self.uow:
            for provider in self.providers:
                rec = provider.get_recommendation(student_id)
                if rec:
                    if isinstance(rec, list):
                        recommendations.extend(rec)
                    else:
                        recommendations.append(rec)
                    
        # Sort by priority ascending (1 is highest priority)
        recommendations.sort(key=lambda x: x.get("priority", 99))
        return recommendations
