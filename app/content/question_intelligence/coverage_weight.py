from typing import Dict, Any
from .models import QuestionIntelligence, EducationalIntent

class CoverageWeightCalculator:
    """
    Calculates a 0.0 to 1.0 normalized score representing a question's contribution
    weight towards covering a learning unit.
    """
    
    def calculate_weight(self, question: Dict[str, Any], intel: QuestionIntelligence) -> float:
        # Base weight based on specific instructions
        q_type = str(question.get("question_type", "")).upper()
        intent = intel.intent
        
        base_weight = 0.15
        
        if q_type == "DEFINITION" or intent == EducationalIntent.DEFINITION:
            base_weight = 0.10
        elif q_type == "RECALL" or intent == EducationalIntent.FACT:
            base_weight = 0.15
        elif q_type == "FILL_BLANK":
            base_weight = 0.15
        elif q_type == "CONCEPT" or intent == EducationalIntent.CONCEPT:
            base_weight = 0.15
        elif q_type == "OBSERVATION" or intent == EducationalIntent.OBSERVATION:
            base_weight = 0.20
        elif q_type in ["MCQ", "MULTIPLE_CHOICE"]:
            base_weight = 0.20
        elif q_type == "REASONING" or intent == EducationalIntent.REASON:
            base_weight = 0.40
            
        return base_weight
