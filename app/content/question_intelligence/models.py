from enum import Enum
from dataclasses import dataclass, field
from typing import List

class BloomLevel(Enum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"

class CognitiveLevel(Enum):
    RECALL = "RECALL"
    RECOGNITION = "RECOGNITION"
    UNDERSTANDING = "UNDERSTANDING"
    OBSERVATION = "OBSERVATION"
    COMPARISON = "COMPARISON"
    CAUSE_EFFECT = "CAUSE_EFFECT"
    REASONING = "REASONING"
    APPLICATION = "APPLICATION"
    ANALYSIS = "ANALYSIS"
    EVALUATION = "EVALUATION"
    CREATION = "CREATION"

class EducationalIntent(Enum):
    DEFINITION = "DEFINITION"
    FACT = "FACT"
    CONCEPT = "CONCEPT"
    PROCESS = "PROCESS"
    OBSERVATION = "OBSERVATION"
    REASON = "REASON"
    APPLICATION = "APPLICATION"
    COMPARISON = "COMPARISON"
    CLASSIFICATION = "CLASSIFICATION"
    TRUE_FALSE = "TRUE_FALSE"
    MCQ = "MCQ"
    FILL_BLANK = "FILL_BLANK"
    SEQUENCE = "SEQUENCE"
    NUMERIC = "NUMERIC"

@dataclass
class QuestionIntelligence:
    bloom_level: BloomLevel
    cognitive_level: CognitiveLevel
    intent: EducationalIntent
    voice_score: int
    speaking_time: float
    thinking_time: float
    cluster_id: str
    question_hash: str
    cluster_name: str = ""
    session_tags: List[str] = field(default_factory=list)
    voice_expected_keywords: List[str] = field(default_factory=list)
    supported_answer_modes: List[str] = field(default_factory=list)
    prerequisite_concepts: List[str] = field(default_factory=list)
    misconception_tags: List[str] = field(default_factory=list)
    normalized_concept: str = ""
    question_purpose: str = "Teaching"
    progression_level: int = 1
    estimated_time: int = 5
    production_score: int = 0
    coverage_weight: float = 0.0
    metadata_score: int = 0
