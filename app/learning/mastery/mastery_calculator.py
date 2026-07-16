from app.constants.mastery import MasteryStatus, MASTERY_THRESHOLDS

class MasteryCalculator:
    def calculate_new_mastery(self, previous_mastery: float, evaluation_score: float, confidence: float, difficulty_weight: float = 1.0) -> float:
        """
        Calculates updated mastery using a weighted scoring model.
        """
        # Base jump depends on correctness (evaluation score)
        if evaluation_score >= 0.8:
            # Positive gain
            gain = 0.10 * difficulty_weight * confidence
            new_mastery = previous_mastery + gain
        else:
            # Loss, dampened by difficulty (losing a hard question penalizes less)
            loss = 0.05 / difficulty_weight
            new_mastery = previous_mastery - loss
            
        return max(0.0, min(1.0, new_mastery))

    def determine_status(self, mastery_percentage: float) -> MasteryStatus:
        if mastery_percentage >= MASTERY_THRESHOLDS["MASTERED_START"]:
            return MasteryStatus.MASTERED
        elif mastery_percentage >= MASTERY_THRESHOLDS["PRACTICING_START"]:
            return MasteryStatus.PRACTICING
        elif mastery_percentage > MASTERY_THRESHOLDS["LEARNING_START"]:
            return MasteryStatus.LEARNING
        return MasteryStatus.NEW
