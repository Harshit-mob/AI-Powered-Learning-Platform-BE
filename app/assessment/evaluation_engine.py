from typing import Any
from app.assessment.models.dto import AnswerSubmission, EvaluationResult

class EvaluationEngine:
    def evaluate(self, submission: AnswerSubmission, expected_answer: Any, question_type: str, acceptable_answers: list = None) -> EvaluationResult:
        """
        Evaluates a submitted answer deterministically.
        Does not interact with repositories or mastery engine.
        """
        is_correct = False
        score = 0.0
        evaluation_method = "EXACT_MATCH"
        matched_answer = str(submission.provided_answer)
        
        if question_type != "VOICE_MATCH":
            # Unify text match for all types including TRUE_FALSE and MCQ
            expected = str(expected_answer).strip().lower()
            provided = str(submission.provided_answer).strip().lower()
            
            acceptables = [expected]
            if acceptable_answers:
                acceptables.extend([str(a).strip().lower() for a in acceptable_answers])
                
            for acc in acceptables:
                if acc and provided == acc:
                    is_correct = True
                    score = 1.0
                    break
                elif acc and (provided in acc or acc in provided):
                    is_correct = True # Partial lenient match
                    score = 0.5
                    evaluation_method = "PARTIAL_MATCH"
                    # Don't break here, in case a later acceptable answer is an EXACT match
            
            # Re-check if we found an exact match to override partial
            if score == 1.0:
                evaluation_method = "EXACT_MATCH"
        # Voice match and others would use specialized deterministic routines
        elif question_type == "VOICE_MATCH":
            is_correct = True if submission.confidence_rating and submission.confidence_rating > 0.8 else False
            score = submission.confidence_rating or 0.0
            evaluation_method = "VOICE_CONFIDENCE"
            
        return EvaluationResult(
            session_id=submission.session_id,
            question_id=submission.question_id,
            student_id=submission.student_id,
            is_correct=is_correct,
            evaluation_score=score,
            evaluation_method=evaluation_method,
            matched_answer=matched_answer,
            voice_score=submission.confidence_rating,
            response_time=submission.time_taken_seconds,
            hints_used=submission.hints_used
        )
