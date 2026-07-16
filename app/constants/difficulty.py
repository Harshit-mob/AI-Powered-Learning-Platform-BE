from enum import Enum

class QuestionDifficulty(str, Enum):
    VERY_EASY = "VERY_EASY"
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    VERY_HARD = "VERY_HARD"

class DifficultyPreference(str, Enum):
    GENTLE = "GENTLE"
    STANDARD = "STANDARD"
    CHALLENGING = "CHALLENGING"
