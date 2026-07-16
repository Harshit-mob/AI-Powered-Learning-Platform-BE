from app.constants.difficulty import QuestionDifficulty
from app.constants.session import SessionType

class DifficultySelector:
    def determine_target_difficulty(self, mastery_percentage: float, session_type: str) -> QuestionDifficulty:
        """
        Determines the target difficulty for a session purely via deterministic rules.
        """
        if session_type == SessionType.RECOVERY.value or mastery_percentage < 0.30:
            return QuestionDifficulty.VERY_EASY
            
        if session_type == SessionType.CHALLENGE.value:
            return QuestionDifficulty.VERY_HARD

        if mastery_percentage < 0.60:
            return QuestionDifficulty.EASY
        elif mastery_percentage < 0.80:
            return QuestionDifficulty.MEDIUM
        elif mastery_percentage < 0.95:
            return QuestionDifficulty.HARD
        else:
            return QuestionDifficulty.VERY_HARD
