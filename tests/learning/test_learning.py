import pytest
import uuid
from datetime import datetime

from app.assessment.models.dto import EvaluationResult
from app.learning.mastery.mastery_calculator import MasteryCalculator
from app.learning.mastery.confidence_calculator import ConfidenceCalculator
from app.learning.scheduler.sm2 import SM2Scheduler
from app.constants.mastery import MasteryStatus

def test_confidence_calculator():
    calc = ConfidenceCalculator()
    
    # Fast, correct, no hints
    result_high = EvaluationResult(
        session_id=uuid.uuid4(),
        question_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        is_correct=True,
        evaluation_score=1.0,
        evaluation_method="EXACT",
        matched_answer="A",
        response_time=5.0,
        hints_used=0
    )
    conf_high = calc.calculate_confidence(result_high)
    assert conf_high >= 0.9
    
    # Correct but slow and hints used
    result_low_conf = EvaluationResult(
        session_id=uuid.uuid4(),
        question_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        is_correct=True,
        evaluation_score=1.0,
        evaluation_method="EXACT",
        matched_answer="A",
        response_time=20.0,
        hints_used=2
    )
    conf_low = calc.calculate_confidence(result_low_conf)
    assert conf_low < 0.8
    
    # Incorrect
    result_incorrect = EvaluationResult(
        session_id=uuid.uuid4(),
        question_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        is_correct=False,
        evaluation_score=0.0,
        evaluation_method="EXACT",
        matched_answer="A",
        response_time=10.0,
        hints_used=0
    )
    conf_incorrect = calc.calculate_confidence(result_incorrect)
    assert conf_incorrect <= 0.2

def test_mastery_calculator():
    calc = MasteryCalculator()
    
    # Base increase
    new_mastery = calc.calculate_new_mastery(previous_mastery=0.4, evaluation_score=1.0, confidence=0.9, difficulty_weight=1.0)
    assert new_mastery > 0.4
    
    # Decrease on wrong answer
    new_mastery_wrong = calc.calculate_new_mastery(previous_mastery=0.4, evaluation_score=0.0, confidence=0.2, difficulty_weight=1.0)
    assert new_mastery_wrong < 0.4
    
    # Status progression
    assert calc.determine_status(0.1) == MasteryStatus.NEW
    assert calc.determine_status(0.3) == MasteryStatus.LEARNING
    assert calc.determine_status(0.6) == MasteryStatus.PRACTICING
    assert calc.determine_status(0.9) == MasteryStatus.MASTERED

def test_sm2_scheduler():
    scheduler = SM2Scheduler()
    
    # First correct
    state1 = scheduler.calculate_next_review(evaluation_score=1.0, previous_interval=0.0, previous_ease=2.5, successive_correct=0)
    assert state1["interval"] == 1.0
    assert state1["successive_correct"] == 1
    
    # Second correct
    state2 = scheduler.calculate_next_review(evaluation_score=1.0, previous_interval=1.0, previous_ease=state1["ease_factor"], successive_correct=1)
    assert state2["interval"] == 6.0
    assert state2["successive_correct"] == 2
    
    # Fail
    state_fail = scheduler.calculate_next_review(evaluation_score=0.0, previous_interval=6.0, previous_ease=state2["ease_factor"], successive_correct=2)
    assert state_fail["interval"] == 1.0
    assert state_fail["successive_correct"] == 0
    assert state_fail["ease_factor"] < state2["ease_factor"]
