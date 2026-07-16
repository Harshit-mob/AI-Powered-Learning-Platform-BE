from typing import Dict, Any, List

class AnswerModeValidator:
    """
    Deterministically assigns and validates supported_answer_modes based on 
    the question_type.
    """
    
    def validate(self, question: Dict[str, Any]) -> List[str]:
        q_type = str(question.get("question_type", "")).strip().upper()
        
        # Base modes supported by almost all textual questions
        modes = ["VOICE", "TEXT"]
        
        if q_type == "MCQ":
            modes.append("MCQ")
        elif q_type == "TRUE_FALSE":
            modes.append("BOOLEAN")
            
        return modes
