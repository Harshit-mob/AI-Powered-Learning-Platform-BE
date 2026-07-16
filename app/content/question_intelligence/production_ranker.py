import logging
from typing import Dict, Any

from .models import QuestionIntelligence
from .config import IntelligenceConfig
from .utils import count_words

logger = logging.getLogger(__name__)

class ProductionRanker:
    """
    Calculates a 0-100 Production Score indicating how safe and effective
    the question is to serve to live users.
    """
    def __init__(self, config: IntelligenceConfig):
        self.config = config

    def rank(self, question: Dict[str, Any], quality_score: int, partial_intel: QuestionIntelligence) -> int:
        score = 0.0
        
        # 1. Base Quality (30 points max)
        score += (quality_score / 100.0) * 30.0
        
        # 2. Voice Friendliness (10 points max)
        score += (partial_intel.voice_score / 100.0) * 10.0
        
        # 3. Coverage Weight (15 points max)
        cov_weight = getattr(partial_intel, "coverage_weight", 0.5)
        score += (cov_weight * 15.0)
        
        # 4. Hint Quality (15 points max)
        h1 = str(question.get("hint_level_1", "")).lower()
        h2 = str(question.get("hint_level_2", "")).lower()
        
        # Penalize bad hints
        h_score = 15.0
        bad_phrases = ["starts with", "think carefully", "the answer is", "remember that"]
        for phrase in bad_phrases:
            if phrase in h1 or phrase in h2:
                h_score -= 5.0
                
        # Bonus for good length hints
        if 5 < count_words(h1) < 20 and 5 < count_words(h2) < 20:
            pass # Keep points
        else:
            h_score -= 5.0
            
        score += max(0, h_score)
        
        # 5. Grammar & Clarity (15 points max)
        q_text = str(question.get("question", "")).strip()
        g_score = 15.0
        if q_text and not q_text[0].isupper():
            g_score -= 5.0
        if q_text and not q_text.endswith("?"):
            g_score -= 5.0
        score += max(0, g_score)
        
        # 6. Distractor Quality & Difficulty Alignment (15 points max)
        q_type = str(question.get("question_type", "")).upper()
        d_score = 15.0
        if q_type == "MCQ":
            options = question.get("mcq_options", [])
            if len(options) == 4:
                # Penalize "all of the above" or "none of the above"
                opts_lower = [str(o).lower() for o in options]
                for o in opts_lower:
                    if "all of the above" in o or "none of the above" in o:
                        d_score -= 10.0
            else:
                d_score -= 15.0
        else:
            # Not MCQ, evaluate based on acceptable answers
            acc = question.get("acceptable_answers", [])
            if len(acc) < 3:
                d_score -= 5.0
                
        score += max(0, d_score)
        
        final_score = score
        return int(max(0, min(100, final_score)))
