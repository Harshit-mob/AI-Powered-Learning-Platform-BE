from app.assessment.models.dto import EvaluationResult

class ConfidenceCalculator:
    def calculate_confidence(self, result: EvaluationResult) -> float:
        """
        Calculates a new confidence score from 0.0 to 1.0 based on response characteristics.
        """
        confidence = 0.5
        
        # Correctness is the baseline
        if result.is_correct:
            confidence = 0.8
            # Bonus for high evaluation score (e.g., precise voice match)
            if result.evaluation_score >= 0.9:
                confidence += 0.1
                
            # Penalty for excessive hints
            if result.hints_used > 0:
                confidence -= (result.hints_used * 0.1)
                
            # Fast response time (assuming < 10 seconds is fast for generic questions)
            if result.response_time < 10.0:
                confidence += 0.1
                
        else:
            confidence = 0.2
            if result.evaluation_score > 0.0:
                confidence += (result.evaluation_score * 0.3)
                
        # Ensure bounds
        return max(0.0, min(1.0, confidence))
