import logging
from typing import Dict, Any, Tuple

from .models import BloomLevel, EducationalIntent

logger = logging.getLogger(__name__)

class DiversityClusterer:
    """
    Deterministically clusters semantically similar questions together.
    The Session Builder uses this cluster_id to ensure a student doesn't receive
    functionally identical questions back-to-back.
    """
    def cluster(self, question: Dict[str, Any], bloom_level: BloomLevel, intent: EducationalIntent) -> Tuple[str, str]:
        from .concept_normalizer import ConceptNormalizer
        
        orig_concept = str(question.get("concept", "")).strip()
        q_type = str(question.get("question_type", "")).strip().lower()
        bloom = bloom_level.value.lower()
        
        # Get normalized concept
        normalizer = ConceptNormalizer()
        normalized_concept = normalizer.normalize(question)
        
        difficulty = int(question.get("difficulty", 2))
        diff_str = "Easy" if difficulty <= 2 else "Medium" if difficulty == 3 else "Hard"
        
        # Readable Cluster ID
        c_id = f"{normalized_concept}_{difficulty}_{bloom}_{q_type}"
        
        # Readable Cluster Name
        if not orig_concept:
            c_name = "Unknown Concept"
        else:
            # Format: Concept - Difficulty - Bloom - Question Family
            concept_title = orig_concept.replace("_", " ").title()
            q_type_title = q_type.replace("_", " ").title()
            bloom_title = bloom.title()
            c_name = f"{concept_title} - {diff_str} - {bloom_title} - {q_type_title}"
            
        return c_id, c_name
