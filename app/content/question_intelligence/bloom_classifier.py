import logging
from typing import Dict, Any

from .models import BloomLevel
from .utils import normalize_text

logger = logging.getLogger(__name__)

class BloomClassifier:
    """
    Deterministically classifies a question into Bloom's Taxonomy based on
    question wording, question type, and complexity.
    """
    def classify(self, question: Dict[str, Any]) -> BloomLevel:
        q_text = normalize_text(str(question.get("text", question.get("question", ""))))
        q_text_lower = q_text.lower()
        
        words = set(q_text.split())
        
        # Exact requested verb mappings
        remember_verbs = {"define", "identify", "name", "list", "recall"}
        understand_verbs = {"explain", "describe", "summarize", "classify"}
        apply_verbs = {"use", "solve", "demonstrate"}
        analyze_verbs = {"compare", "infer", "distinguish", "analyze"}
        evaluate_verbs = {"justify", "defend", "argue", "evaluate"}
        create_verbs = {"design", "invent", "propose", "create"}
        
        level = BloomLevel.REMEMBER
        
        # Priority mapping from highest Bloom to lowest
        if words.intersection(create_verbs):
            level = BloomLevel.CREATE
        elif words.intersection(evaluate_verbs):
            level = BloomLevel.EVALUATE
        elif words.intersection(analyze_verbs) or "why" in words or "distinguish" in q_text_lower:
            level = BloomLevel.ANALYZE
        elif words.intersection(apply_verbs) or "predict outcome" in q_text_lower or "calculate" in words:
            level = BloomLevel.APPLY
        elif words.intersection(understand_verbs) or "how does" in q_text_lower:
            level = BloomLevel.UNDERSTAND
        elif words.intersection(remember_verbs) or "what is" in q_text_lower or "what are" in q_text_lower:
            level = BloomLevel.REMEMBER
        else:
            # Fallback based on question heuristics if no specific verb is found
            if "why" in words or "how" in words:
                level = BloomLevel.UNDERSTAND
            elif "which" in words or "what" in words:
                level = BloomLevel.REMEMBER
            
        return level
