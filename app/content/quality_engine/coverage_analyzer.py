import re
from typing import Dict, Any, List, Tuple
from functools import lru_cache

class CoverageAnalyzer:
    def __init__(self):
        self._pattern = re.compile(r'[^\w\s]')

    @lru_cache(maxsize=1024)
    def _normalize(self, text: str) -> str:
        if not text: return ""
        return " ".join(self._pattern.sub('', text).lower().split())

    def analyze(self, learning_unit: Dict[str, Any], accepted_questions: List[Dict[str, Any]]) -> Tuple[float, List[str], List[str], Dict[str, int], bool]:
        """
        Returns (coverage_percentage, covered_concepts, missing_concepts, category_distribution, is_balanced)
        """
        keywords = learning_unit.get("keywords", [])
        if not keywords:
            # Fallback if no keywords, extract from objective
            objective = self._normalize(learning_unit.get("learning_objective", ""))
            # Just rough split for fallback
            keywords = [w for w in objective.split() if len(w) > 4]
            if not keywords:
                return 100.0, [], []
                
        norm_kws = [self._normalize(k) for k in keywords]
        
        # Build text corpus from accepted questions
        corpus_parts = []
        for q in accepted_questions:
            corpus_parts.append(self._normalize(str(q.get("concept", ""))))
            corpus_parts.append(self._normalize(str(q.get("question", ""))))
            corpus_parts.append(self._normalize(str(q.get("expected_answer", ""))))
            
        corpus = " ".join(corpus_parts)
        
        covered = []
        missing = []
        
        for idx, k in enumerate(norm_kws):
            original = keywords[idx]
            if k in corpus:
                covered.append(original)
            else:
                missing.append(original)
                
        percentage = (len(covered) / len(keywords)) * 100.0 if keywords else 100.0
        
        # 10-Class Taxonomy Distribution
        distribution = {
            "Definition": 0, "Concept": 0, "Recall": 0, "Understanding": 0, 
            "Application": 0, "Reasoning": 0, "Misconception Check": 0, 
            "Scenario": 0, "Real-life Application": 0, "Assessment": 0
        }
        
        for q in accepted_questions:
            cat = self._classify_question(q)
            distribution[cat] += 1
            
        is_balanced = True
        total = len(accepted_questions)
        if total > 5:
            for cat, count in distribution.items():
                if count / total > 0.40: # No category can dominate more than 40%
                    is_balanced = False
                    
        return percentage, covered, missing, distribution, is_balanced

    def _classify_question(self, q: Dict[str, Any]) -> str:
        q_type = str(q.get("question_type", "")).upper()
        bloom = str(q.get("bloom_level", "")).upper()
        cog = str(q.get("cognitive_level", "")).upper()
        text = str(q.get("question", "")).lower() + " " + str(q.get("text", "")).lower()
        diff = int(q.get("difficulty", 1))
        
        is_scenario = any(name in text for name in ["riya", "rohan", "aisha", "rahul", "student", "imagine", "notices"])
        
        if diff >= 4:
            return "Assessment"
        if q_type == "TRUE_FALSE" or "misconception" in text:
            return "Misconception Check"
        if q_type == "DEFINITION":
            return "Definition"
        if is_scenario:
            return "Scenario"
        if "everyday" in text or "real-life" in text or "real life" in text or "home" in text:
            return "Real-life Application"
        if cog == "REASONING" or bloom in ["ANALYZE", "EVALUATE", "CREATE"]:
            return "Reasoning"
        if bloom == "APPLY":
            return "Application"
        if bloom == "UNDERSTAND":
            return "Understanding"
        if bloom == "REMEMBER" or q_type == "RECALL":
            return "Recall"
            
        return "Concept"
