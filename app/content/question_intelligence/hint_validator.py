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
                
            import re
            expected = str(question.get("expected_answer", "")).lower().strip()
            correct_opt = str(question.get("correct_option", "")).lower().strip()
            is_trivial = expected in ["yes", "no", "true", "false", "y", "n"] or len(expected) <= 2
            
            gives_away = False
            if not is_trivial:
                escaped_expected = re.escape(expected)
                gives_away = bool(re.search(rf"\b{escaped_expected}\b", hint))
                if correct_opt and len(correct_opt) > 2 and correct_opt not in ["yes", "no", "true", "false", "y", "n"]:
                    escaped_correct = re.escape(correct_opt)
                    gives_away = gives_away or bool(re.search(rf"\b{escaped_correct}\b", hint))
            
            if gives_away:
                return False, f"Hint gives away the answer directly: '{expected}' in '{question.get(level)}'"
                
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
