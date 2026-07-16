from typing import List, Dict
from app.models.quiz import Question

class QuestionRanker:
    def rank_questions(self, candidates: List[Question], target_difficulty: str, count: int, taxonomy_distribution: Dict[str, float]) -> List[Question]:
        """
        Ranks candidate questions based on deterministic rules:
        - Difficulty fit
        - Diversity
        - Freshness
        """
        def get_score(q: Question) -> int:
            score = 0
            # Difficulty matching
            if q.difficulty_level == target_difficulty:
                score += 10
            
            # Additional heuristic scoring would go here (e.g. freshness check, bloom level mapping)
            return score

        # Sort by deterministic score descending. Tie break deterministically by UUID if needed.
        ranked = sorted(candidates, key=lambda q: (get_score(q), str(q.id)), reverse=True)
        
        # Select the top `count`
        selected = ranked[:count]
        
        # Enforce Bloom progression (lower taxonomy first)
        bloom_order = {"REMEMBER": 1, "UNDERSTAND": 2, "APPLY": 3, "ANALYZE": 4, "EVALUATE": 5, "CREATE": 6}
        selected = sorted(selected, key=lambda q: bloom_order.get(q.bloom_level, 99))
        
        return selected
