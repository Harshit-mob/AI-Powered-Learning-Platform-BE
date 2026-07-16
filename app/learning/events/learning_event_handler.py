import uuid
from typing import List
from datetime import datetime

from app.repositories.base.unit_of_work import UnitOfWork
from app.assessment.models.dto import EvaluationResult
from app.learning.models.dto import LearningOutcome, LearningEventPayload
from app.learning.mastery.mastery_engine import MasteryEngine
from app.learning.scheduler.review_scheduler import ReviewScheduler
from app.learning.progress.progress_tracker import ProgressTracker
from app.constants.events import EventName, EntityType

class LearningEventHandler:
    """
    Consumes assessment payloads, orchestrates learning calculations, 
    persists updates via UoW, and returns an immutable LearningOutcome DTO.
    """
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.mastery_engine = MasteryEngine(uow)
        self.scheduler = ReviewScheduler(uow)
        self.progress_tracker = ProgressTracker(uow)

    def process_session_completion(self, session_id: uuid.UUID, student_id: uuid.UUID, evaluations: List[EvaluationResult]) -> LearningOutcome:
        # 1. Calculate mastery changes (pure business logic mapping)
        mastery_updates = self.mastery_engine.process_evaluations(student_id, evaluations)
        
        # 2. Calculate schedule changes
        review_updates = self.scheduler.process_reviews(student_id, evaluations)
        
        # 3. Generate summary
        progress_summary = self.progress_tracker.generate_summary(student_id, mastery_updates)
        
        # 4. Generate events
        events = []
        for mu in mastery_updates:
            events.append(LearningEventPayload(
                event_name=EventName.MASTERY_UPDATED.value,
                entity_type=EntityType.CONCEPT.value,
                entity_id=str(mu.concept_id),
                payload={
                    "student_id": str(student_id),
                    "old_mastery": mu.old_mastery,
                    "new_mastery": mu.new_mastery,
                    "status": mu.new_status
                }
            ))
            
        events.append(LearningEventPayload(
            event_name=EventName.SESSION_FINISHED.value,
            entity_type=EntityType.SESSION.value,
            entity_id=str(session_id),
            payload={
                "student_id": str(student_id),
                "summary": progress_summary
            }
        ))
        
        # 5. Persist everything atomically
        with self.uow:
            # Upsert mastery
            for mu in mastery_updates:
                self.uow.mastery.upsert_mastery(
                    student_id=student_id, 
                    concept_id=mu.concept_id, 
                    mastery_data={
                        "mastery_percentage": mu.new_mastery,
                        "confidence_score": mu.confidence_score,
                        "status": mu.new_status,
                        "last_practiced": datetime.utcnow()
                    }
                )
            
            # Upsert schedules
            for ru in review_updates:
                schedule = self.uow.schedules.first({"student_id": student_id, "concept_id": ru.concept_id})
                if schedule:
                    self.uow.schedules.update_schedule(schedule.id, {
                        "next_review": datetime.fromisoformat(ru.next_review),
                        "interval": ru.interval,
                        "ease_factor": ru.ease_factor,
                        "successive_correct_reviews": schedule.successive_correct_reviews + 1 # simplistic update
                    })
                else:
                    self.uow.schedules.create_schedule({
                        "student_id": student_id,
                        "concept_id": ru.concept_id,
                        "scheduler_type": "SM2",
                        "next_review": datetime.fromisoformat(ru.next_review),
                        "interval": ru.interval,
                        "ease_factor": ru.ease_factor,
                        "successive_correct_reviews": 1
                    })
            
            # Save events to log
            event_dicts = [{
                "event_name": e.event_name,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "payload": e.payload
            } for e in events]
            self.uow.events.append_many(event_dicts)
            
            # Commit the unified transaction
            self.uow.commit()

        # 6. Return standard immutable outcome DTO for the next domain
        return LearningOutcome(
            session_id=session_id,
            student_id=student_id,
            mastery_updates=mastery_updates,
            review_updates=review_updates,
            generated_events=events,
            progress_summary=progress_summary
        )
