import uuid
import random
from datetime import datetime
from typing import List, Dict
from app.runtime.session.models.student_context import StudentContext
from app.runtime.session.session_types import SessionType
from app.models.quiz import Question

class LearningUnitCoverage:
    """
    Ranks Learning Units based on StudentContext.
    Priority:
    1. Never Practiced
    2. Frequently Incorrect
    3. Low Mastery
    4. Weak Confidence
    5. Mastered
    """
    
    def rank_learning_units(
        self, 
        lu_map: Dict[uuid.UUID, List[Question]], 
        context: StudentContext,
        session_type: SessionType,
        session_id: uuid.UUID
    ) -> List[uuid.UUID]:
        
        def get_priority_score(lu_id: uuid.UUID) -> float:
            status = context.status_by_lu.get(lu_id, "NEW")
            mastery = context.mastery_by_lu.get(lu_id, 0.0)
            confidence = context.confidence_by_lu.get(lu_id, 0.0)
            
            score = 0.0
            
            # 1. Never Practiced
            if status == "NEW" or mastery == 0.0:
                score += 1000.0
                
            # 2. Frequently Incorrect (Phase 1: simplistic approximation via low mastery/status)
            if status == "LEARNING" and mastery < 0.3:
                score += 800.0
                
            # 3. Low Mastery
            if mastery < 0.5:
                score += (1.0 - mastery) * 500.0
                
            # 4. Weak Confidence
            if confidence < 0.5:
                score += (1.0 - confidence) * 200.0
                
            # 5. Mastered
            if status == "MASTERED" or mastery >= 0.85:
                score -= 500.0
                
            # Seeded Randomization for tie-breaking
            seed_str = f"{context.student_id}_{lu_id}_{session_type.value}_{session_id}"
            rng = random.Random(seed_str)
            jitter = rng.uniform(0.0, 0.99)
            
            return score + jitter

        # Sort LU IDs by their priority score descending
        ranked_lus = sorted(lu_map.keys(), key=get_priority_score, reverse=True)
        return ranked_lus
