import uuid
from dataclasses import dataclass, field
from typing import Dict
from app.runtime.session.models.student_context import StudentContext
from app.runtime.session.question_variant_selector import QuestionVariantSelector, VariantScore
from app.runtime.session.session_types import SessionType
from app.models.quiz import Question
# Import LearningUnit to resolve SQLAlchemy mapper registry
from app.models.course import LearningUnit

def test_concept_level_variant_deduplication():
    # 1. Setup Student Context
    # Simulate a student who answered a question belonging to 'concept_a' correctly in the past.
    student_id = uuid.uuid4()
    context = StudentContext(student_id=student_id)
    context.correct_concepts["concept_a"] = True
    context.concept_attempts["concept_a"] = 1
    
    # 2. Setup Candidates
    # Candidate 1: Sharing the same concept ('concept_a')
    q1 = Question(
        id=uuid.uuid4(),
        learning_unit_id=uuid.uuid4(),
        normalized_concept="concept_a",
        text="What is the sure test of magnetism? (MCQ variant)",
        difficulty=2,
        bloom_level="REMEMBER"
    )
    
    # Candidate 2: A different concept ('concept_b') never attempted
    q2 = Question(
        id=uuid.uuid4(),
        learning_unit_id=uuid.uuid4(),
        normalized_concept="concept_b",
        text="Describe Lodestone.",
        difficulty=3,
        bloom_level="UNDERSTAND"
    )

    selector = QuestionVariantSelector()
    
    # 3. Test for standard practice session (deduplication should occur)
    session_id = uuid.uuid4()
    eligible = selector.select_variants([q1, q2], context, SessionType.DAILY_PRACTICE, session_id)
    
    # Verify q1 (concept_a) is filtered out because the concept was already answered correctly.
    # Only q2 (concept_b) should be returned as eligible.
    eligible_q_ids = [v.question.id for v in eligible]
    assert q2.id in eligible_q_ids
    assert q1.id not in eligible_q_ids
    
    # 4. Test for revision session (both should be returned, as revision allows reviewing correct concepts)
    revision_eligible = selector.select_variants([q1, q2], context, SessionType.REVISION, session_id)
    revision_q_ids = [v.question.id for v in revision_eligible]
    assert q1.id in revision_q_ids
    assert q2.id in revision_q_ids
