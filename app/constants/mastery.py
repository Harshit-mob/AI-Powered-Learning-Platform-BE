from enum import Enum

class MasteryStatus(str, Enum):
    NEW = "NEW"
    LEARNING = "LEARNING"
    PRACTICING = "PRACTICING"
    MASTERED = "MASTERED"
    REVIEW = "REVIEW"

MASTERY_THRESHOLDS = {
    "LEARNING_START": 0.0,
    "PRACTICING_START": 0.4,
    "MASTERED_START": 0.85
}
