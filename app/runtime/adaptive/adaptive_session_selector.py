import uuid
from typing import List
from app.runtime.models.dto import NextSessionInfo, RecommendationItem
from app.constants.session import SessionType

class AdaptiveSessionSelector:
    def select_next_session(self, student_id: uuid.UUID, recommendations: List[RecommendationItem]) -> NextSessionInfo:
        """
        Deterministically selects the absolute next best session type to launch.
        """
        if not recommendations:
            return NextSessionInfo(
                session_type=SessionType.PRACTICE.value,
                reason="Default practice progression.",
                target_content_ids=[]
            )
            
        top_rec = recommendations[0]
        
        return NextSessionInfo(
            session_type=top_rec.recommended_session_type,
            reason=top_rec.reason,
            target_content_ids=[top_rec.target_content_id]
        )
