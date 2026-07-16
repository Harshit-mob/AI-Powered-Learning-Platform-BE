import logging
from typing import Dict, Any

from .models import EducationalIntent
from .utils import normalize_text

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    Deterministically detects the educational intent of a question.
    """
    def classify(self, question: Dict[str, Any]) -> EducationalIntent:
        q_type = str(question.get("question_type", "")).strip().upper()
        q_text = normalize_text(str(question.get("question", "")))
        
        q_text_lower = q_text.lower()
        
        # 1. Intent-based mappings from Question Type
        type_intent_map = {
            "DEFINITION": EducationalIntent.DEFINITION,
            "OBSERVATION": EducationalIntent.OBSERVATION,
            "REASONING": EducationalIntent.REASON,
            "COMPARISON": EducationalIntent.COMPARISON,
            "APPLICATION": EducationalIntent.APPLICATION,
            "SEQUENCE": EducationalIntent.SEQUENCE,
            "NUMERIC": EducationalIntent.NUMERIC
        }
        if q_type in type_intent_map:
            return type_intent_map[q_type]
            
        # 2. Text heuristics (Primary)
        if "predict" in q_text_lower or "what will happen" in q_text_lower or "infer" in q_text_lower:
            return EducationalIntent.REASON
        if "define" in q_text_lower or "what is meant by" in q_text_lower:
            return EducationalIntent.DEFINITION
        if "process" in q_text_lower or "steps" in q_text_lower or "how to" in q_text_lower or "sequence" in q_text_lower:
            return EducationalIntent.PROCESS
        if "classify" in q_text_lower or "group" in q_text_lower or "type of" in q_text_lower:
            return EducationalIntent.CLASSIFICATION
        if "identify" in q_text_lower or "which of" in q_text_lower:
            return EducationalIntent.CONCEPT
        if "fact" in q_text_lower:
            return EducationalIntent.FACT
            
        # 3. Explicit structural mappings (Only as fallbacks)
        if q_type == "MCQ": return EducationalIntent.MCQ
        if q_type == "TRUE_FALSE": return EducationalIntent.TRUE_FALSE
        if q_type == "FILL_BLANK": return EducationalIntent.FILL_BLANK
        
        return EducationalIntent.CONCEPT
