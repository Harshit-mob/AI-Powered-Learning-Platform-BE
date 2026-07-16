import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class HintValidator:
    """
    Validates hints for educational quality.
    Rejects 'fill in the blank' style letter hints and replaces them.
    """
    
    BAD_PHRASES = [
        "starts with",
        "starts with letter",
        "begins with",
        "first letter",
        "initial letter",
        "look carefully",
        "look carefully",
        "think harder",
        "read again",
        "think carefully",
        "the answer is",
        "consider the concept",
        "apply your knowledge",
        "practical scenario",
        "remember the lesson",
        "look closely",
        "apply the concept",
        "consider"
    ]
    
    def validate_and_repair(self, question: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Returns (is_valid, warning_message).
        Mutates the question to repair bad hints.
        """
        repaired = False
        warnings = []
        
        for level in ["hint_level_1", "hint_level_2"]:
            hint = str(question.get(level, "")).lower()
            
            if not hint:
                # If there's no hint, we don't necessarily repair it here, 
                # but the Metadata Score Engine will deduct points for missing hints.
                continue
                
            if any(bad_phrase in hint for bad_phrase in self.BAD_PHRASES):
                original = question.get(level, "")
                if level == "hint_level_1":
                    concept_name = str(question.get("concept", "the topic")).replace("_", " ").title()
                    question[level] = f"Recall the primary characteristics of {concept_name}."
                else:
                    q_type = str(question.get("question_type", "")).replace("_", " ").title()
                    question[level] = f"Focus on the exact {q_type} required to answer this."
                    
                repaired = True
                warnings.append(f"Repaired poor educational hint '{original}' in {level}")
                
        if repaired:
            return True, "; ".join(warnings)
        return True, ""
