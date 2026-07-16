from typing import List
from app.models.quiz import Question

class PedagogicalSequencer:
    """
    Orders questions into a deterministic pedagogical flow:
    Warm-up -> Recall -> Understand -> Apply -> Challenge
    Absolutely no random.shuffle().
    """
    
    def _get_pedagogical_score(self, q: Question) -> int:
        bloom = str(getattr(q, "bloom_level", "RECALL")).upper()
        difficulty = getattr(q, "difficulty", 3)
        
        # 1. Warm-up (EASY)
        if difficulty <= 2:
            return 1
            
        # 2. Recall (MEDIUM + RECALL)
        if bloom in ["REMEMBER", "RECALL"]:
            return 2
            
        # 3. Understand (MEDIUM + UNDERSTAND)
        if bloom in ["UNDERSTAND", "COMPREHENSION"]:
            return 3
            
        # 4. Apply (APPLICATION)
        if bloom in ["APPLY", "APPLICATION"]:
            return 4
            
        # 5. Challenge (ANALYSIS, EVALUATION, CREATION, or HARD)
        return 5

    def sequence(self, questions: List[Question]) -> List[Question]:
        # Sort entirely by pedagogical score ascending.
        # This forces the progression Warm-up -> Recall -> Understand -> Apply -> Challenge
        return sorted(questions, key=self._get_pedagogical_score)
