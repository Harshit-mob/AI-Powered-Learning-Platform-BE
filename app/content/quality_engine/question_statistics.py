from collections import defaultdict
from typing import Dict, Any, List

class QuestionStatistics:
    def __init__(self):
        self.question_types = defaultdict(int)
        self.difficulties = defaultdict(int)
        
    def add_question(self, q: Dict[str, Any]):
        q_type = str(q.get("question_type", "")).strip().upper().replace(" ", "_").replace("/", "_")
        diff = q.get("difficulty", 0)
        self.question_types[q_type] += 1
        self.difficulties[f"Difficulty {diff}"] += 1
        
    def get_type_distribution(self) -> Dict[str, int]:
        return dict(self.question_types)
        
    def get_difficulty_distribution(self) -> Dict[str, int]:
        return dict(self.difficulties)
        
    def check_skewness(self) -> List[str]:
        warnings = []
        total = sum(self.difficulties.values())
        if total > 0:
            if self.difficulties.get("Difficulty 1", 0) / total > 0.8:
                warnings.append("Difficulty distribution is heavily skewed towards Difficulty 1")
            elif self.difficulties.get("Difficulty 4", 0) / total > 0.8:
                warnings.append("Difficulty distribution is heavily skewed towards Difficulty 4")
        return warnings
