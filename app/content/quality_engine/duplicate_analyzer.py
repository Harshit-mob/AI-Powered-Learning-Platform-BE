import re
from typing import Dict, Any
from collections import defaultdict
from difflib import SequenceMatcher
from functools import lru_cache

from .validation_models import QualityConfig

class DuplicateAnalyzer:
    def __init__(self, config: QualityConfig):
        self.config = config
        self._pattern = re.compile(r'[^\w\s]')
        # Bucket by: unit_id -> (concept) -> list of questions
        self._buckets = defaultdict(lambda: defaultdict(list))
        # Explanation starters tracker: starter -> count
        self._expl_starters = defaultdict(int)
        self._total_questions = 0

    @lru_cache(maxsize=4096)
    def _normalize(self, text: str) -> str:
        if not text: return ""
        return " ".join(self._pattern.sub('', text).lower().split())

    def check_duplicate(self, q: Dict[str, Any]) -> bool:
        """
        Returns True if the question is considered a duplicate.
        """
        unit_id = str(q.get("learning_unit_id", "unknown"))
        concept = self._normalize(str(q.get("concept", "")))
        q_type = self._normalize(str(q.get("question_type", "")))
        exp_ans = self._normalize(str(q.get("expected_answer", "")))
        eval_method = self._normalize(str(q.get("evaluation_method", "")))
        q_text = self._normalize(str(q.get("question", "")))

        # We don't just bucket by q_type anymore, we bucket by concept to prevent semantic duplicates across types
        bucket = self._buckets[unit_id][concept]

        for existing in bucket:
            # 1. Reject if text similarity is too high (lexical diversity)
            similarity = SequenceMatcher(None, q_text, existing["question"]).ratio()
            if similarity >= 0.70:
                return True
                
            same_answer = (exp_ans and existing["expected_answer"] == exp_ans and exp_ans not in ["true", "false", "yes", "no"])
            words_new = q_text.split()
            words_old = existing["question"].split()
            same_opening = (len(words_new) > 2 and len(words_old) > 2 and words_new[:2] == words_old[:2])
            
            # If they share the exact same expected answer AND same opening words, they are too similar.
            # We allow different questions with the same answer to support language learning / vocabulary drills.
            if same_answer and same_opening:
                return True
                
            # If they are exactly identical questions
            if existing["question"] == q_text:
                return True

        # Not a duplicate, add to bucket
        bucket.append({
            "question": q_text,
            "expected_answer": exp_ans,
            "bloom_level": q.get("bloom_level"),
            "cognitive_level": q.get("cognitive_level"),
            "evaluation_method": eval_method
        })
        
        # Track explanation starters for diversity (bypassed duplicate rejection for common prefix phrasing)
        expl = str(q.get("full_explanation", "")).strip()
        if expl:
            words = expl.split()
            if len(words) >= 2:
                starter = f"{words[0]} {words[1]}".lower()
                self._expl_starters[starter] += 1
                
        self._total_questions += 1
        
        return False
