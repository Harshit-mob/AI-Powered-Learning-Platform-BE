from typing import List
import uuid
from app.runtime.models.dto import RecommendationItem
from app.learning.models.dto import LearningOutcome
from app.constants.session import SessionType

class RecommendationRules:
    def generate(self, outcome: LearningOutcome) -> List[RecommendationItem]:
        """
        Applies deterministic rules to generate recommendations based on the learning outcome.
        """
        recommendations = []
        
        # Rule 1: Weak concepts need review/recovery
        for mastery_update in outcome.mastery_updates:
            if mastery_update.new_mastery < 0.4 and mastery_update.new_status in ["NEW", "LEARNING"]:
                recommendations.append(RecommendationItem(
                    id=uuid.uuid4(),
                    priority=100, # Highest priority
                    reason=f"Mastery dropped or remains low ({int(mastery_update.new_mastery*100)}%) for concept.",
                    target_content_id=mastery_update.concept_id,
                    target_content_type="CONCEPT",
                    recommended_session_type=SessionType.RECOVERY.value
                ))
            elif mastery_update.new_mastery >= 0.85 and mastery_update.old_mastery < 0.85:
                recommendations.append(RecommendationItem(
                    id=uuid.uuid4(),
                    priority=50,
                    reason="You mastered a concept! Ready for a challenge?",
                    target_content_id=mastery_update.concept_id,
                    target_content_type="CONCEPT",
                    recommended_session_type=SessionType.CHALLENGE.value
                ))
        
        # Rule 2: Spaced Repetition Due
        for review in outcome.review_updates:
            # If interval is very short, it's due soon
            if review.interval <= 1.0:
                recommendations.append(RecommendationItem(
                    id=uuid.uuid4(),
                    priority=80,
                    reason="Due for spaced repetition review to prevent forgetting.",
                    target_content_id=review.concept_id,
                    target_content_type="CONCEPT",
                    recommended_session_type=SessionType.REVISION.value
                ))

        # Sort by priority descending
        return sorted(recommendations, key=lambda x: x.priority, reverse=True)
