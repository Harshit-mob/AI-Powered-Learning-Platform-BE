import uuid
from typing import Dict, Any
from app.repositories.base.unit_of_work import UnitOfWork
from app.services.analytics.models.dto import QuestionQualityReport

class QuestionAnalyticsService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def process_answer_event(self, question_id: uuid.UUID, is_correct: bool, time_taken: float, hints_used: int, voice_score: float = None):
        """
        Incrementally updates the question analytics read-model based on a single answer event.
        """
        with self.uow:
            analytics = self.uow.question_analytics.get_by_question_id(question_id)
            if not analytics:
                # Assuming increment_attempt handles creation if it doesn't exist.
                self.uow.question_analytics.increment_attempt(question_id)
                analytics = self.uow.question_analytics.get_by_question_id(question_id)
            else:
                self.uow.question_analytics.increment_attempt(question_id)
                
            # Running average calculations
            attempts = analytics.total_attempts
            prev_acc = analytics.accuracy_rate
            new_acc = prev_acc + ((1.0 if is_correct else 0.0) - prev_acc) / attempts
            self.uow.question_analytics.update_accuracy(question_id, new_acc)
            
            prev_time = analytics.average_response_time or 0.0
            new_time = prev_time + (time_taken - prev_time) / attempts
            self.uow.question_analytics.update_response_time(question_id, new_time)
            
            if voice_score is not None:
                prev_vs = analytics.average_voice_score or 0.0
                new_vs = prev_vs + (voice_score - prev_vs) / attempts
                self.uow.question_analytics.update_voice_score(question_id, new_vs)
            
            self.uow.commit()

    def process_skip_event(self, question_id: uuid.UUID):
        with self.uow:
            analytics = self.uow.question_analytics.get_by_question_id(question_id)
            if analytics:
                attempts = analytics.total_attempts + 1 # Include skip as attempt for rate calc
                prev_skip = analytics.skip_rate
                new_skip = prev_skip + (1.0 - prev_skip) / attempts
                self.uow.question_analytics.update_skip_rate(question_id, new_skip)
                self.uow.commit()
