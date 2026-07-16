import pytest
import uuid
from typing import List

from app.models.quiz import Question
from app.constants.difficulty import QuestionDifficulty
from app.constants.session import SessionType
from app.assessment.models.dto import AnswerSubmission
from app.assessment.strategies.practice_strategy import PracticeStrategy
from app.assessment.difficulty_selector import DifficultySelector
from app.assessment.question_ranker import QuestionRanker
from app.assessment.session_builder import SessionBuilder
from app.assessment.evaluation_engine import EvaluationEngine

def test_difficulty_selector():
    selector = DifficultySelector()
    
    # Test Recovery
    assert selector.determine_target_difficulty(0.20, SessionType.PRACTICE) == QuestionDifficulty.VERY_EASY
    assert selector.determine_target_difficulty(0.80, SessionType.RECOVERY) == QuestionDifficulty.VERY_EASY
    
    # Test Challenge
    assert selector.determine_target_difficulty(0.50, SessionType.CHALLENGE) == QuestionDifficulty.VERY_HARD
    
    # Test Normal Progression
    assert selector.determine_target_difficulty(0.50, SessionType.PRACTICE) == QuestionDifficulty.EASY
    assert selector.determine_target_difficulty(0.70, SessionType.PRACTICE) == QuestionDifficulty.MEDIUM
    assert selector.determine_target_difficulty(0.90, SessionType.PRACTICE) == QuestionDifficulty.HARD
    assert selector.determine_target_difficulty(0.98, SessionType.PRACTICE) == QuestionDifficulty.VERY_HARD

def test_question_ranker():
    ranker = QuestionRanker()
    
    # Create mock questions
    q1 = Question(id=uuid.uuid4(), learning_unit_id=uuid.uuid4(), difficulty_level=QuestionDifficulty.EASY.value, bloom_level="REMEMBER")
    q2 = Question(id=uuid.uuid4(), learning_unit_id=uuid.uuid4(), difficulty_level=QuestionDifficulty.MEDIUM.value, bloom_level="UNDERSTAND")
    q3 = Question(id=uuid.uuid4(), learning_unit_id=uuid.uuid4(), difficulty_level=QuestionDifficulty.EASY.value, bloom_level="APPLY")
    
    candidates = [q3, q2, q1]
    
    ranked = ranker.rank_questions(candidates, target_difficulty=QuestionDifficulty.EASY.value, count=2, taxonomy_distribution={})
    
    assert len(ranked) == 2
    # Q1 and Q3 match difficulty. Q1 has lower bloom level ("REMEMBER"), so it should come first.
    assert ranked[0].id == q1.id
    assert ranked[1].id == q3.id

def test_session_builder():
    builder = SessionBuilder()
    student_id = uuid.uuid4()
    content_id = uuid.uuid4()
    
    q1 = Question(id=uuid.uuid4(), learning_unit_id=uuid.uuid4(), question_text="Q1", question_type="MCQ", difficulty_level="EASY", bloom_level="REMEMBER", cognitive_level="RECALL")
    
    session = builder.build_session(
        student_id=student_id,
        content_id=content_id,
        session_type=SessionType.PRACTICE,
        questions=[q1],
        estimated_minutes=5
    )
    
    assert session.student_id == student_id
    assert session.content_id == content_id
    assert session.session_type == SessionType.PRACTICE
    assert session.question_count == 1
    assert len(session.questions) == 1
    assert session.questions[0].id == q1.id

def test_evaluation_engine_mcq():
    engine = EvaluationEngine()
    
    sub = AnswerSubmission(
        session_id=uuid.uuid4(),
        question_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        provided_answer="A",
        time_taken_seconds=12.5,
        hints_used=0,
        device_type="web"
    )
    
    # Correct Answer
    result1 = engine.evaluate(submission=sub, expected_answer="A", question_type="MCQ")
    assert result1.is_correct is True
    assert result1.evaluation_score == 1.0
    
    # Incorrect Answer
    result2 = engine.evaluate(submission=sub, expected_answer="B", question_type="MCQ")
    assert result2.is_correct is False
    assert result2.evaluation_score == 0.0

def test_evaluation_engine_fill_blank_partial():
    engine = EvaluationEngine()
    
    sub = AnswerSubmission(
        session_id=uuid.uuid4(),
        question_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        provided_answer="photosynthesis process",
        time_taken_seconds=15.0,
        hints_used=1,
        device_type="mobile"
    )
    
    # Partial lenient match
    result = engine.evaluate(submission=sub, expected_answer="photosynthesis", question_type="FILL_BLANK")
    assert result.is_correct is True
    assert result.evaluation_score == 0.5
    assert result.evaluation_method == "PARTIAL_MATCH"
    assert result.hints_used == 1
