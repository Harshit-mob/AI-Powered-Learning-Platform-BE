import re
from typing import Dict, Any
from functools import lru_cache

from .validation_models import QualityConfig

class QuestionQualityAnalyzer:
    def __init__(self, config: QualityConfig):
        self.config = config
        self._pattern = re.compile(r'[^\w\s]')

    @lru_cache(maxsize=1024)
    def _word_count(self, text: str) -> int:
        if not text: return 0
        return len(self._pattern.sub('', text).lower().split())

    def analyze_voice_friendliness(self, question_text: str) -> int:
        wc = self._word_count(question_text)
        score = 100
        # Optimal 6-12 words
        if wc > self.config.max_question_words:
            score -= (wc - self.config.max_question_words) * 10
        elif wc > self.config.preferred_question_words:
            score -= (wc - self.config.preferred_question_words) * 5
        if wc < 6:
            score -= (6 - wc) * 5
            
        if ";" in question_text or ":" in question_text:
            score -= 20
            
        return max(0, min(100, score))

    def analyze(self, q: Dict[str, Any], unit_diversity_count: int) -> int:
        score = 0
        
        # Voice (25 max)
        v_score = self.analyze_voice_friendliness(str(q.get("question", "")))
        score += (v_score / 100) * 25
        
        # Metadata (5 max)
        if q.get("learning_unit_id") and q.get("learning_objective"):
            score += 5
            
        # Hints (10 max)
        h1 = str(q.get("hint_level_1", "")).lower()
        h2 = str(q.get("hint_level_2", "")).lower()
        if h1 and h2 and h1 != h2:
            score += 10
            
        # Explanation (10 max)
        exp = str(q.get("full_explanation", ""))
        exp_wc = self._word_count(exp)
        if 10 <= exp_wc <= 60:
            score += 10
        elif exp_wc > 0:
            score += 5
            
        # Answer Quality (15 max)
        acc_ans = q.get("acceptable_answers", [])
        if len(acc_ans) >= 5:
            score += 15
        elif len(acc_ans) >= 2:
            score += 10
            
        # Question Diversity (15 max)
        if unit_diversity_count <= 2:
            score += 15
            
        # Difficulty (5 max)
        diff = q.get("difficulty", 2)
        if 1 <= diff <= 4:
            score += 5
            
        # Keywords (5 max)
        kws = q.get("keywords", [])
        if len(kws) >= 2:
            score += 5
            
        # Evaluation Method (10 max)
        if q.get("evaluation_method"):
            score += 10
            
        return int(score)
