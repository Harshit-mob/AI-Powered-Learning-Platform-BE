import logging
from typing import Dict, Any, Tuple

from .models import CognitiveLevel
from .config import IntelligenceConfig
from .utils import count_words

logger = logging.getLogger(__name__)

class VoiceAnalyzer:
    """
    Determines if a question is suitable for voice-first interactions and 
    estimates speaking/thinking times.
    """
    def __init__(self, config: IntelligenceConfig):
        self.config = config

    def analyze(self, question: Dict[str, Any], cognitive_level: CognitiveLevel) -> Tuple[int, float, float]:
        q_text = str(question.get("question", ""))
        ans_text = str(question.get("expected_answer", ""))
        
        q_wc = count_words(q_text)
        ans_wc = count_words(ans_text)
        
        # Base score starts based on answer length buckets
        if ans_wc == 1:
            score = 100 # Single word -> 95-100
        elif ans_wc <= 4:
            score = 95  # Short phrase -> 85-95
        elif ans_wc <= 12:
            score = 85  # Reasoning -> 70-85
        else:
            score = 80  # Long Explanation -> 60-80
            
        # 1. Sentence length (deduct up to 5 points from base bucket)
        if q_wc > 15:
            score -= min(5, (q_wc - 15) * 1)
            
        # 2. Number of syllables (approximation: words > 3 chars * 1.5)
        syllables_est = sum(1.5 for w in q_text.split() if len(w) > 3)
        if syllables_est > 10:
            score -= min(5, (syllables_est - 10) * 0.5)
            
        # 3. Pronunciation difficulty (long words)
        words = [w.strip('.,?":;()') for w in q_text.split()]
        difficult_words = [w for w in words if len(w) > 7]
        score -= min(5, len(difficult_words) * 1)
        
        # 4. Ambiguity / Question type penalties
        q_type = str(question.get("question_type", "")).strip().upper()
        if q_type == "MCQ" or q_type == "MULTIPLE_CHOICE":
            score -= 10
        if q_type == "FILL_BLANK":
            if q_text.count("_") > 1:
                score -= 10
                
        # Constrain to the absolute buckets depending on answer length
        if ans_wc == 1:
            voice_score = max(95, min(100, int(score)))
        elif ans_wc <= 4:
            voice_score = max(85, min(95, int(score)))
        elif ans_wc <= 12:
            voice_score = max(70, min(85, int(score)))
        else:
            voice_score = max(60, min(80, int(score)))
        
        # 2. Speaking Time (seconds)
        # Child speaking speed ~130 WPM
        wps = 130.0 / 60.0
        base_time = q_wc / wps if wps > 0 else 0
        pauses = (q_text.count(',') * 0.4) + (q_text.count('.') * 0.8) + (q_text.count('?') * 0.8)
        speaking_time = base_time + pauses
        
        # 3. Thinking Time (seconds) - NOTE: This is overridden by TimeEstimator later
        thinking_time = 0.0
        
        return voice_score, round(speaking_time, 2), round(thinking_time, 2)
