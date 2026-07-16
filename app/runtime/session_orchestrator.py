import uuid
from typing import List
from pydantic import BaseModel
from app.assessment.models.dto import AnswerSubmission, EvaluationResult
from app.learning.models.dto import LearningOutcome
from app.runtime.models.dto import PersonalizationOutcome

from app.assessment.evaluation_engine import EvaluationEngine
from app.learning.events.learning_event_handler import LearningEventHandler
from app.runtime.personalization_engine import PersonalizationEngine

class RuntimeSessionResult(BaseModel):
    evaluation_results: List[EvaluationResult]
    learning_outcome: LearningOutcome
    personalization_outcome: PersonalizationOutcome

    class Config:
        frozen = True

class RuntimeOrchestrator:
    """
    Coordinates domain execution to prevent domains from directly calling one another.
    """
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory
        self.eval_engine = EvaluationEngine()
        # Orchestrator handles domain crossing. We don't redefine generation here, 
        # it is called directly from the SessionEngine during API invocation.

    def process_session_submission(self, session_id: uuid.UUID, student_id: uuid.UUID, submissions: List[AnswerSubmission]) -> RuntimeSessionResult:
        evaluations = []
        
        # 1. Assessment Domain: Evaluate (Pure Logic, No DB required for basic eval)
        # Assuming we have expected answers fetched via UoW for real implementation
        with self.uow_factory() as uow:
            for sub in submissions:
                question = uow.questions.get_by_id(sub.question_id)
                # In real scenario, question options/answer would be checked. Mocking expected answer here.
                expected_answer = question.options[0] if question and question.options else "A" 
                q_type = question.question_type if question else "MCQ"
                
                result = self.eval_engine.evaluate(sub, expected_answer, q_type)
                evaluations.append(result)
                
                # Save Response
                uow.responses.save_response({
                    "session_id": sub.session_id,
                    "question_id": sub.question_id,
                    "student_id": sub.student_id,
                    "provided_answer": sub.provided_answer,
                    "is_correct": result.is_correct,
                    "time_taken_seconds": sub.time_taken_seconds
                })
            
            # Close session
            uow.sessions.finish_session(session_id, {"end_time": "NOW"})
            uow.commit()

        # 2. Learning Domain: Calculate Mastery & Schedule using its own UoW boundary
        with self.uow_factory() as uow:
            learning_handler = LearningEventHandler(uow)
            learning_outcome = learning_handler.process_session_completion(session_id, student_id, evaluations)

        # 3. Personalization Domain: Generate Next Path using its own UoW boundary
        with self.uow_factory() as uow:
            personalization_engine = PersonalizationEngine(uow)
            personalization_outcome = personalization_engine.generate_personalization(learning_outcome)

        # 4. Return Final Aggregated Result
        return RuntimeSessionResult(
            evaluation_results=evaluations,
            learning_outcome=learning_outcome,
            personalization_outcome=personalization_outcome
        )
