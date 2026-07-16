from typing import Dict, Any, List
from app.repositories.base.unit_of_work import UnitOfWork
from app.services.analytics.question.question_analytics import QuestionAnalyticsService
from app.services.analytics.student.student_analytics import StudentAnalyticsService
from app.constants.events import EventName

class AnalyticsDispatcher:
    """
    Consumes asynchronous events and routes them to specific analytical projection builders.
    Supports deterministic batch replay for rebuilding read models.
    """
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    def dispatch(self, event_name: str, payload: Dict[str, Any]):
        """Routes a single event."""
        with self.uow_factory() as uow:
            qa_service = QuestionAnalyticsService(uow)
            student_service = StudentAnalyticsService(uow)
            
            if event_name == "QuestionAnswered":
                qa_service.process_answer_event(
                    question_id=payload.get("question_id"),
                    is_correct=payload.get("is_correct"),
                    time_taken=payload.get("time_taken_seconds", 0),
                    hints_used=payload.get("hints_used", 0)
                )
            
            elif event_name == EventName.MASTERY_UPDATED.value:
                student_service.process_mastery_event(
                    student_id=payload.get("student_id"),
                    concept_id=payload.get("concept_id"), # In practice from the aggregate ID
                    old_mastery=payload.get("old_mastery"),
                    new_mastery=payload.get("new_mastery")
                )

    def replay_events(self, events: List[Dict[str, Any]]):
        """
        Rebuilds projections by replaying historical events deterministically.
        """
        for event in events:
            self.dispatch(event["event_name"], event["payload"])
