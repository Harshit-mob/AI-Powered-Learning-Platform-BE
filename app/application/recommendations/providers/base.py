from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid
from app.repositories.base.unit_of_work import UnitOfWork

class RecommendationProvider(ABC):
    """Base class for all recommendation providers."""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @abstractmethod
    def get_recommendation(self, student_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Returns a recommendation card dictionary if applicable, else None.
        Must include keys:
        - title
        - priority
        - estimated_duration
        - question_count
        - xp_reward
        - status
        - reason
        - session_type
        - content_type
        - content_ids
        """
        pass
