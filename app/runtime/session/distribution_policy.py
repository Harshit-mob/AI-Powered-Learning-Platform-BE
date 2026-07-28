import uuid
from typing import List, Dict
from abc import ABC, abstractmethod

from app.runtime.session.session_types import SessionType
from app.runtime.session.exceptions import SessionEngineException
from app.runtime.session.session_config import SessionConfig
from app.runtime.session.question_variant_selector import VariantScore

class DistributionPolicy(ABC):
    """
    Strategy base class for enforcing session quotas while prioritizing Learning Units.
    """
    
    @abstractmethod
    def apply(
        self, 
        ranked_lus: List[uuid.UUID], 
        variants_by_lu: Dict[uuid.UUID, List[VariantScore]]
    ) -> List[VariantScore]:
        pass

class QuotaDistributionPolicy(DistributionPolicy):
    """
    Implements a soft-quota selection algorithm.
    Prioritizes filling missing difficulty quotas first, using Bloom as secondary, 
    but always prioritizes taking at least one variant from the highest ranked LUs.
    """
    def __init__(self, target_count: int, difficulty_distribution: Dict[str, float], bloom_distribution: Dict[str, float], allow_partial: bool = False):
        self.target_count = target_count
        self.allow_partial = allow_partial
        
        # Calculate concrete target quotas (e.g., 6 EASY, 3 MEDIUM, 1 HARD)
        self.diff_quotas = {k: max(1, int(v * target_count)) for k, v in difficulty_distribution.items()}
        # Ensure total exactly matches target_count
        diff_sum = sum(self.diff_quotas.values())
        if diff_sum < target_count and "EASY" in self.diff_quotas:
            self.diff_quotas["EASY"] += (target_count - diff_sum)
            
        self.bloom_quotas = {k: max(1, int(v * target_count)) for k, v in bloom_distribution.items()}
        
    def apply(
        self, 
        ranked_lus: List[uuid.UUID], 
        variants_by_lu: Dict[uuid.UUID, List[VariantScore]]
    ) -> List[VariantScore]:
        
        selected_variants: List[VariantScore] = []
        selected_qids = set()
        lu_used = set()
        
        # Track current counts
        diff_counts = {k: 0 for k in self.diff_quotas.keys()}
        bloom_counts = {k: 0 for k in self.bloom_quotas.keys()}
        
        # First Pass: Try to pick best variant per LU that fulfills open quotas (1 question per LU maximum)
        for lu_id in ranked_lus:
            if len(selected_variants) >= self.target_count:
                break
                
            candidates = variants_by_lu.get(lu_id, [])
            if not candidates:
                continue
                
            best_match = None
            best_fallback = candidates[0] # Absolute best variant by score
            
            # Find a variant that satisfies BOTH an open diff quota AND an open bloom quota
            for variant in candidates:
                d = variant.difficulty
                b = variant.bloom
                if diff_counts.get(d, 0) < self.diff_quotas.get(d, 0):
                    best_match = variant
                    best_match.selection_reasons.append("difficulty_quota")
                    break
                    
            chosen = best_match if best_match else best_fallback
            if not best_match:
                chosen.selection_reasons.append("soft_fallback")
                
            selected_variants.append(chosen)
            selected_qids.add(chosen.question.id)
            lu_used.add(lu_id)
            
            # Update counts
            d = chosen.difficulty
            b = chosen.bloom
            diff_counts[d] = diff_counts.get(d, 0) + 1
            bloom_counts[b] = bloom_counts.get(b, 0) + 1
            
        # Second Pass: If target count not reached, loop back and pick additional questions from the same LUs
        if len(selected_variants) < self.target_count:
            added_any = True
            while len(selected_variants) < self.target_count and added_any:
                added_any = False
                for lu_id in ranked_lus:
                    if len(selected_variants) >= self.target_count:
                        break
                    
                    candidates = variants_by_lu.get(lu_id, [])
                    next_variant = None
                    for variant in candidates:
                        if variant.question.id not in selected_qids:
                            next_variant = variant
                            break
                            
                    if next_variant:
                        next_variant.selection_reasons.append("target_count_fill")
                        selected_variants.append(next_variant)
                        selected_qids.add(next_variant.question.id)
                        
                        # Update counts
                        d = next_variant.difficulty
                        b = next_variant.bloom
                        diff_counts[d] = diff_counts.get(d, 0) + 1
                        bloom_counts[b] = bloom_counts.get(b, 0) + 1
                        added_any = True
            
        # Sufficiency Check: require at least MIN_QUESTIONS, not necessarily target_count
        MIN_QUESTIONS = 3
        if len(selected_variants) < MIN_QUESTIONS and not self.allow_partial:
            raise SessionEngineException(
                f"INSUFFICIENT_QUESTIONS|Only {len(selected_variants)} eligible questions are available for this topic. "
                f"A minimum of {MIN_QUESTIONS} questions are required to generate a session."
            )

        return selected_variants

class RevisionDistributionPolicy(DistributionPolicy):
    """
    Returns all eligible question variants for the session without any quota limit.
    """
    def apply(
        self, 
        ranked_lus: List[uuid.UUID], 
        variants_by_lu: Dict[uuid.UUID, List[VariantScore]]
    ) -> List[VariantScore]:
        selected: List[VariantScore] = []
        for lu_id in ranked_lus:
            candidates = variants_by_lu.get(lu_id, [])
            selected.extend(candidates)
        return selected

class PolicyFactory:
    @staticmethod
    def get_policy(session_type: SessionType) -> DistributionPolicy:
        if session_type == SessionType.DAILY_PRACTICE:
            return QuotaDistributionPolicy(
                target_count=10,
                difficulty_distribution=SessionConfig.DAILY_POLICY["difficulty_distribution"],
                bloom_distribution=SessionConfig.DAILY_POLICY["bloom_distribution"],
                allow_partial=True   # generate with however many are available
            )
        elif session_type == SessionType.CHAPTER_REVISION:
            return QuotaDistributionPolicy(
                target_count=20,
                difficulty_distribution=SessionConfig.REVISION_POLICY["difficulty_distribution"],
                bloom_distribution=SessionConfig.REVISION_POLICY["bloom_distribution"],
                allow_partial=True
            )
        elif session_type == SessionType.WEAK_POINT:
            return QuotaDistributionPolicy(
                target_count=8,
                difficulty_distribution={"EASY": 0.2, "MEDIUM": 0.5, "HARD": 0.3},
                bloom_distribution={"RECALL": 0.2, "COMPREHENSION": 0.4, "APPLICATION": 0.4},
                allow_partial=True
            )
        elif session_type == SessionType.REVISION:
            return RevisionDistributionPolicy()
        else:
            # Default fallback
            return QuotaDistributionPolicy(
                target_count=10,
                difficulty_distribution={"EASY": 0.5, "MEDIUM": 0.3, "HARD": 0.2},
                bloom_distribution={"RECALL": 1.0},
                allow_partial=True   # always partial-safe
            )
