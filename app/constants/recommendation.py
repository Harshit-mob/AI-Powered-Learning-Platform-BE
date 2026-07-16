from enum import Enum

class RecommendationSource(str, Enum):
    MASTERY_ENGINE = "MASTERY_ENGINE"
    TEACHER = "TEACHER"
    ADAPTIVE_ENGINE = "ADAPTIVE_ENGINE"

class RecommendationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class CompletionStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    IGNORED = "IGNORED"
