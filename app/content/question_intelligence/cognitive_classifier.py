import logging
from typing import Dict, Any

from .models import CognitiveLevel
from .utils import normalize_text

logger = logging.getLogger(__name__)

class CognitiveClassifier:
    """
    Deterministically classifies the primary cognitive skill required to answer the question.
    """
    def classify(self, question: Dict[str, Any], bloom_level: str = None) -> CognitiveLevel:
        q_type = str(question.get("question_type", "")).strip().upper()
        q_text = normalize_text(str(question.get("text", question.get("question", ""))))
        
        # 1. Text-based heuristic primary check
        q_text_lower = q_text.lower()
        words = set(q_text_lower.split())
        
        if "compare" in words or "difference" in q_text_lower:
            return CognitiveLevel.COMPARISON
        if "predict" in words or "what will happen" in q_text_lower:
            return CognitiveLevel.REASONING
        if "why" in words or "because" in q_text_lower or "result of" in q_text_lower:
            return CognitiveLevel.CAUSE_EFFECT
        if "reason" in words or "conclude" in words:
            return CognitiveLevel.REASONING
        if "explain" in words or "how" in words:
            return CognitiveLevel.UNDERSTANDING
        if "apply" in words or "if we" in q_text_lower:
            return CognitiveLevel.APPLICATION
        if "observe" in words or "notice" in words:
            return CognitiveLevel.OBSERVATION
        
        # 2. Type-based classification fallback
        type_mapping = {
            "RECALL": CognitiveLevel.RECALL,
            "DEFINITION": CognitiveLevel.RECALL,
            "UNDERSTANDING": CognitiveLevel.UNDERSTANDING,
            "APPLICATION": CognitiveLevel.APPLICATION,
            "OBSERVATION": CognitiveLevel.OBSERVATION,
            "COMPARISON": CognitiveLevel.COMPARISON,
            "CAUSE_EFFECT": CognitiveLevel.CAUSE_EFFECT,
            "REASONING": CognitiveLevel.REASONING,
            "MCQ": CognitiveLevel.RECOGNITION,
            "TRUE_FALSE": CognitiveLevel.RECOGNITION
        }
        
        if q_type in type_mapping:
            return type_mapping[q_type]
            
        if "identify" in words or "what is" in q_text_lower or "define" in q_text_lower:
            predicted = CognitiveLevel.RECALL
        else:
            predicted = CognitiveLevel.UNDERSTANDING
            
        # 3. Deterministic Bloom Consistency Override
        # Never allow invalid Bloom/Cognitive mappings.
        if bloom_level:
            b_upper = bloom_level.upper()
            if b_upper == "REMEMBER":
                if predicted not in [CognitiveLevel.RECALL, CognitiveLevel.RECOGNITION]:
                    predicted = CognitiveLevel.RECALL
            elif b_upper == "UNDERSTAND":
                predicted = CognitiveLevel.UNDERSTANDING
            elif b_upper == "APPLY":
                predicted = CognitiveLevel.APPLICATION
            elif b_upper == "ANALYZE":
                predicted = CognitiveLevel.ANALYSIS
            elif b_upper == "EVALUATE":
                predicted = CognitiveLevel.EVALUATION
            elif b_upper == "CREATE":
                predicted = CognitiveLevel.CREATION
                
        return predicted
