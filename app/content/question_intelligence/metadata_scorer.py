from typing import Dict, Any
from .models import QuestionIntelligence

class MetadataScorer:
    """
    Deterministically calculates a 0-100 score based on the completeness and 
    presence of metadata fields on the question.
    """
    
    def calculate_score(self, question: Dict[str, Any], intel: QuestionIntelligence) -> int:
        score = 0
        
        # 1. Base Question Fields (Total: 50)
        if question.get("expected_answer") and str(question.get("expected_answer")).strip():
            score += 10
            
        acceptable = question.get("acceptable_answers", [])
        if isinstance(acceptable, list) and len(acceptable) > 0:
            score += 10
            
        if question.get("hint_level_1") and str(question.get("hint_level_1")).strip():
            score += 5
            
        if question.get("hint_level_2") and str(question.get("hint_level_2")).strip():
            score += 5
            
        if question.get("full_explanation") and str(question.get("full_explanation")).strip():
            score += 10
            
        keywords = question.get("keywords", [])
        if isinstance(keywords, list) and len(keywords) > 0:
            score += 10
            
        # 2. Intelligence Classifications (Total: 15)
        if intel.bloom_level:
            score += 5
        if intel.cognitive_level:
            score += 5
        if intel.intent:
            score += 5
            
        # 3. Derived Analytics & Tags (Total: 25)
        if intel.session_tags and len(intel.session_tags) > 0:
            score += 5
            
        if intel.production_score > 0:
            score += 10
            
        if intel.voice_score > 0:
            score += 10
            
        # 4. Standard Metadata (Total: 10)
        if question.get("difficulty") is not None:
            score += 5
            
        if question.get("evaluation_method") and str(question.get("evaluation_method")).strip():
            score += 5
            
        return min(100, max(0, score))
