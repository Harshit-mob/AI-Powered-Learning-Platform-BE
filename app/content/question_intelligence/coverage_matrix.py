from collections import defaultdict
from typing import Dict, Any, List

from .models import QuestionIntelligence
from .utils import normalize_text

class CoverageMatrix:
    """
    Generates advanced learning analytics for a Learning Unit based on enriched questions.
    """
    def generate(self, learning_unit: Dict[str, Any], questions: List[Dict[str, Any]], intelligence_list: List[QuestionIntelligence]) -> Dict[str, Any]:
        keywords = learning_unit.get("keywords", [])
        norm_kws = [normalize_text(k) for k in keywords]
        
        bloom_dist = defaultdict(int)
        type_dist = defaultdict(int)
        intent_dist = defaultdict(int)
        diff_dist = defaultdict(int)
        
        concept_occurrences = defaultdict(int)
        
        # Build text corpus for keyword coverage
        corpus_parts = []
        
        for q, intel in zip(questions, intelligence_list):
            # Distributions
            bloom_dist[intel.bloom_level.name] += 1
            intent_dist[intel.intent.name] += 1
            
            q_type = str(q.get("question_type", "")).strip().upper()
            type_dist[q_type] += 1
            
            diff = q.get("difficulty", 2)
            diff_dist[f"Difficulty {diff}"] += 1
            
            # Concept tracking
            concept = normalize_text(str(q.get("concept", "")))
            if concept:
                concept_occurrences[concept] += 1
                
            # Corpus
            corpus_parts.append(concept)
            corpus_parts.append(normalize_text(str(q.get("question", ""))))
            corpus_parts.append(normalize_text(str(q.get("expected_answer", ""))))
            
        # Keyword Coverage Analysis
        corpus = " ".join(corpus_parts)
        covered_keywords = []
        missing_keywords = []
        
        for idx, k in enumerate(norm_kws):
            original = keywords[idx]
            if k and k in corpus:
                covered_keywords.append(original)
            else:
                missing_keywords.append(original)
                
        keyword_coverage = (len(covered_keywords) / len(keywords)) * 100.0 if keywords else 100.0
        
        # Weak concepts (tested only once)
        weak_concepts = [c for c, count in concept_occurrences.items() if count == 1]
        
        return {
            "learning_unit_id": str(learning_unit.get("id", learning_unit.get("learning_unit_id", ""))),
            "total_questions": len(questions),
            "keyword_coverage_percent": round(keyword_coverage, 2),
            "covered_keywords": covered_keywords,
            "missing_keywords": missing_keywords,
            "weak_concepts": weak_concepts,
            "bloom_distribution": dict(bloom_dist),
            "intent_distribution": dict(intent_dist),
            "type_distribution": dict(type_dist),
            "difficulty_distribution": dict(diff_dist)
        }
