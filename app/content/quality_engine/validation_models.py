from enum import Enum
from typing import List
from dataclasses import dataclass, field

class ValidationSeverity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class ValidationIssue:
    type: str
    severity: ValidationSeverity
    message: str

@dataclass
class ValidationResult:
    valid: bool
    severity: ValidationSeverity
    quality_score: int
    issues: List[ValidationIssue] = field(default_factory=list)

@dataclass
class QualityConfig:
    quality_threshold: int = 80
    coverage_threshold: int = 95
    voice_threshold: int = 80
    duplicate_similarity: float = 0.90
    preferred_question_words: int = 12
    max_question_words: int = 18
    minimum_questions_per_unit: int = 10
