import uuid
from typing import List

from app.repositories.base.unit_of_work import UnitOfWork
from app.assessment.models.dto import EvaluationResult
from app.learning.models.dto import MasteryUpdatePayload
from app.learning.mastery.mastery_calculator import MasteryCalculator
from app.learning.mastery.confidence_calculator import ConfidenceCalculator

class MasteryEngine:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.mastery_calculator = MasteryCalculator()
        self.confidence_calculator = ConfidenceCalculator()

    def process_evaluations(self, student_id: uuid.UUID, evaluations: List[EvaluationResult]) -> List[MasteryUpdatePayload]:
        """
        Takes raw evaluation results, looks up the corresponding concepts, 
        and calculates mastery jumps deterministically.
        """
        updates = []
        
        with self.uow:
            for eval_result in evaluations:
                question = self.uow.questions.get_by_id(eval_result.question_id)
                if not question:
                    continue
                
                # Assume a direct relation to concept for this MVP (using learning_unit_id as proxy if concept_id missing)
                # In full schema, we'd query uow.concepts
                concept_id = question.learning_unit_id 
                
                # Fetch existing mastery
                current_mastery = self.uow.mastery.get_by_concept(student_id, concept_id)
                prev_mastery_pct = current_mastery.mastery_percentage if current_mastery else 0.0
                prev_status = current_mastery.status if current_mastery else "NEW"
                
                # Calculate confidence and new mastery
                confidence = self.confidence_calculator.calculate_confidence(eval_result)
                
                # A simple heuristic for difficulty weight (Harder = higher weight)
                diff_weight = 1.0
                if question.difficulty_level in ["HARD", "VERY_HARD"]:
                    diff_weight = 1.5
                elif question.difficulty_level in ["VERY_EASY", "EASY"]:
                    diff_weight = 0.8
                
                new_mastery_pct = self.mastery_calculator.calculate_new_mastery(
                    prev_mastery_pct, 
                    eval_result.evaluation_score, 
                    confidence, 
                    diff_weight
                )
                
                new_status = self.mastery_calculator.determine_status(new_mastery_pct)
                
                updates.append(MasteryUpdatePayload(
                    concept_id=concept_id,
                    old_mastery=prev_mastery_pct,
                    new_mastery=new_mastery_pct,
                    old_status=prev_status.value if hasattr(prev_status, "value") else prev_status,
                    new_status=new_status.value if hasattr(new_status, "value") else new_status,
                    confidence_score=confidence
                ))
                
        return updates
