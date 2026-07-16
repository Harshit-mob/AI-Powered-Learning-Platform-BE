from app.repositories.base.unit_of_work import UnitOfWork
from app.learning.models.dto import LearningOutcome
from app.runtime.models.dto import PersonalizationOutcome
from app.runtime.recommendation.recommendation_engine import RecommendationEngine
from app.runtime.learning_path.learning_path_engine import LearningPathEngine
from app.runtime.adaptive.adaptive_session_selector import AdaptiveSessionSelector
from app.runtime.goals.daily_goal_tracker import DailyGoalTracker
from app.runtime.preferences.preference_engine import PreferenceEngine
from app.constants.events import EventName, EntityType

class PersonalizationEngine:
    """
    Orchestrator for the Personalization Domain. Consumes LearningOutcome and produces PersonalizationOutcome.
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.recommendation_engine = RecommendationEngine(uow)
        self.learning_path_engine = LearningPathEngine(uow)
        self.adaptive_selector = AdaptiveSessionSelector()
        self.goal_tracker = DailyGoalTracker(uow)
        self.preference_engine = PreferenceEngine(uow)

    def generate_personalization(self, outcome: LearningOutcome) -> PersonalizationOutcome:
        # 1. Apply Preferences
        preferences = self.preference_engine.get_preference_adjustments(outcome.student_id)
        
        # 2. Track Goals
        goal_progress = self.goal_tracker.track_progress(outcome.student_id, outcome)
        
        # 3. Generate Recommendations
        recommendations = self.recommendation_engine.process(outcome)
        
        # 4. Generate Path
        learning_path = self.learning_path_engine.generate_path(outcome.student_id, recommendations)
        
        # 5. Select Next Session
        next_session = self.adaptive_selector.select_next_session(outcome.student_id, recommendations)
        
        # Emit Domain Events atomically via UoW
        with self.uow:
            event_dicts = [
                {
                    "event_name": EventName.RECOMMENDATION_GENERATED.value,
                    "entity_type": EntityType.STUDENT.value,
                    "entity_id": str(outcome.student_id),
                    "payload": {
                        "recommendations_count": len(recommendations),
                        "next_session_type": next_session.session_type
                    }
                }
            ]
            self.uow.events.append_many(event_dicts)
            self.uow.commit()

        # Output Immutable Result
        return PersonalizationOutcome(
            student_id=outcome.student_id,
            session_id=outcome.session_id,
            recommendations=recommendations,
            next_session=next_session,
            learning_path=learning_path,
            goal_progress=goal_progress,
            preference_adjustments=preferences
        )
