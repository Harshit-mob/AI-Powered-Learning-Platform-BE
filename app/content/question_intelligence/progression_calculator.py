from typing import Dict, Any
from .models import QuestionIntelligence, BloomLevel, EducationalIntent

class ProgressionCalculator:
    """
    Deterministically assigns a progression_level (1-4) representing the 
    learning maturity required for the question.
    """
    
    def calculate(self, question: Dict[str, Any], intel: QuestionIntelligence) -> int:
        # Strictly monotonic progression based on intent and cognitive depth
        intent = intel.intent
        bloom = intel.bloom_level
        q_type = str(question.get("question_type", "")).upper()
        
        # Level 5: Critical Thinking
        if intent in {EducationalIntent.REASON} and bloom == BloomLevel.ANALYZE:
            return 5
            
        # Level 4: Reasoning
        if intent in {EducationalIntent.REASON, EducationalIntent.COMPARISON}:
            return 4
            
        # Level 3: Application & Scenario
        if intent == EducationalIntent.APPLICATION or bloom == BloomLevel.APPLY:
            return 3
            
        # Level 2: Concept, Observation, Classification
        if intent in {EducationalIntent.CONCEPT, EducationalIntent.OBSERVATION, EducationalIntent.CLASSIFICATION, EducationalIntent.PROCESS}:
            return 2
            
        # Level 1: Definition, Vocabulary, Fill blank, True False, Factual Recall
        return 1
