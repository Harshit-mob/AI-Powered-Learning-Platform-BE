import uuid
import random
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from app.runtime.session.models.student_context import StudentContext
from app.runtime.session.session_types import SessionType
from app.models.quiz import Question

@dataclass
class VariantScore:
    question: Question
    score: float
    difficulty: str
    bloom: str
    selection_reasons: List[str] = field(default_factory=list)

class QuestionVariantSelector:
    """
    Scores all question variants for a given Learning Unit.
    Priority:
    1. Never Attempted
    2. Incorrectly Answered
    3. Low Frequency Incorrect
    """
    
    def select_variants(
        self, 
        candidates: List[Question], 
        context: StudentContext,
        session_type: SessionType,
        session_id: uuid.UUID
    ) -> List[VariantScore]:
        
        if not candidates:
            return []
            
        scored_variants: List[VariantScore] = []
        for q in candidates:
            q_id = q.id
            attempts = context.question_attempts.get(q_id, 0)
            is_correct = context.correct_questions.get(q_id, False)
            
            reasons = []
            score = 0.0
            
            # Extract difficulty and bloom safely
            diff_val = getattr(q, "difficulty", 3)
            diff_str = "MEDIUM" if diff_val == 3 else ("EASY" if diff_val <= 2 else "HARD")
            
            bloom_val = str(getattr(q, "bloom_level", "RECALL")).upper()
            if bloom_val in ["REMEMBER", "RECALL"]: bloom_val = "RECALL"
            elif bloom_val in ["UNDERSTAND", "COMPREHENSION"]: bloom_val = "COMPREHENSION"
            elif bloom_val in ["APPLY", "APPLICATION"]: bloom_val = "APPLICATION"
            elif bloom_val in ["ANALYZE", "ANALYSIS"]: bloom_val = "ANALYSIS"
            elif bloom_val in ["EVALUATE", "EVALUATION"]: bloom_val = "EVALUATION"
            elif bloom_val in ["CREATE", "CREATION"]: bloom_val = "CREATION"

            if is_correct:
                score = -1000.0
                reasons.append("exhausted_variant")
            elif attempts == 0:
                score = 100.0
                reasons.append("unseen_variant")
            else:
                score = 50.0 - attempts
                reasons.append("incorrect_variant")
                
            # Seeded Randomization for tie-breaking
            seed_str = f"{context.student_id}_{q.learning_unit_id}_{session_type.value}_{session_id}_{q.id}"
            rng = random.Random(seed_str)
            jitter = rng.uniform(0.0, 0.99)
            final_score = score + jitter
            
            scored_variants.append(VariantScore(
                question=q,
                score=final_score,
                difficulty=diff_str,
                bloom=bloom_val,
                selection_reasons=reasons
            ))
            
        # Sort variants by score descending
        ranked_variants = sorted(scored_variants, key=lambda x: x.score, reverse=True)
        
        # Filter out variants that are absolutely terrible (already correct) unless it's the only option
        # Actually, we let DistributionPolicy handle the fallback if needed, or we just exclude them here.
        eligible_variants = [v for v in ranked_variants if v.score > -500]
        
        # If all were correct, we return nothing, meaning this LU is fully exhausted
        return eligible_variants
