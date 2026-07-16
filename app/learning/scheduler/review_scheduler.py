import uuid
from typing import List
from app.repositories.base.unit_of_work import UnitOfWork
from app.assessment.models.dto import EvaluationResult
from app.learning.models.dto import ReviewUpdatePayload
from app.learning.scheduler.sm2 import SM2Scheduler

class ReviewScheduler:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.scheduler = SM2Scheduler()

    def process_reviews(self, student_id: uuid.UUID, evaluations: List[EvaluationResult]) -> List[ReviewUpdatePayload]:
        updates = []
        
        with self.uow:
            # Using SM2 directly as it is the only supported scheduler for the MVP
            strategy = self.scheduler
            
            for eval_result in evaluations:
                question = self.uow.questions.get_by_id(eval_result.question_id)
                if not question:
                    continue
                
                concept_id = question.learning_unit_id
                
                # Fetch existing schedule
                schedule = self.uow.schedules.first({"student_id": student_id, "concept_id": concept_id})
                prev_interval = schedule.interval if schedule else 1.0
                prev_ease = schedule.ease_factor if schedule else 2.5
                prev_correct = schedule.successive_correct_reviews if schedule else 0
                
                # Calculate new schedule
                new_state = strategy.calculate_next_review(
                    evaluation_score=eval_result.evaluation_score,
                    previous_interval=prev_interval,
                    previous_ease=prev_ease,
                    successive_correct=prev_correct
                )
                
                updates.append(ReviewUpdatePayload(
                    concept_id=concept_id,
                    next_review=new_state["next_review"],
                    interval=new_state["interval"],
                    ease_factor=new_state["ease_factor"]
                ))
                
        return updates
