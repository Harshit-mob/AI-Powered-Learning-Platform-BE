from typing import Dict, Any
from .models import QuestionIntelligence

class PurposeGenerator:
    """
    Deterministically assigns a primary educational purpose to a question.
    Values: Teaching, Practice, Assessment, Revision, Warmup, Challenge.
    """
    
    def generate(self, question: Dict[str, Any], intel: QuestionIntelligence) -> str:
        diff = int(question.get("difficulty", 2))
        q_type = str(question.get("question_type", "")).upper()
        prod_score = getattr(intel, "production_score", 0)
        
        # 1. Strict Mapping based on difficulty
        if diff == 1:
            purpose = "Warmup"
        elif diff == 2:
            purpose = "Practice"
        elif diff == 3:
            purpose = "Assessment"
        elif diff == 4:
            purpose = "Challenge"
        elif diff >= 5:
            purpose = "Mastery"
        else:
            purpose = "Practice"
            
        # No random overrides
        if q_type in ["EXAM", "QUIZ_ONLY"]:
            purpose = "Assessment"
            
        return purpose
