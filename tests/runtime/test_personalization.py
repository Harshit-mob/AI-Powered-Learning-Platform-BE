import pytest
import uuid

from app.learning.models.dto import LearningOutcome, MasteryUpdatePayload, ReviewUpdatePayload
from app.runtime.recommendation.recommendation_rules import RecommendationRules
from app.runtime.learning_path.learning_path_engine import LearningPathEngine
from app.runtime.adaptive.adaptive_session_selector import AdaptiveSessionSelector

def get_mock_outcome(mastery_updates, review_updates) -> LearningOutcome:
    return LearningOutcome(
        session_id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        mastery_updates=mastery_updates,
        review_updates=review_updates,
        generated_events=[],
        progress_summary={}
    )

def test_recommendation_rules_recovery():
    rules = RecommendationRules()
    
    # Simulate weak concept
    outcome = get_mock_outcome(
        mastery_updates=[
            MasteryUpdatePayload(
                concept_id=uuid.uuid4(),
                old_mastery=0.5,
                new_mastery=0.2, # Dropped significantly
                old_status="LEARNING",
                new_status="NEW",
                confidence_score=0.1
            )
        ],
        review_updates=[]
    )
    
    recs = rules.generate(outcome)
    assert len(recs) == 1
    assert recs[0].recommended_session_type == "RECOVERY"
    assert recs[0].priority == 100

def test_recommendation_rules_challenge():
    rules = RecommendationRules()
    
    # Simulate newly mastered concept
    outcome = get_mock_outcome(
        mastery_updates=[
            MasteryUpdatePayload(
                concept_id=uuid.uuid4(),
                old_mastery=0.8,
                new_mastery=0.9,
                old_status="PRACTICING",
                new_status="MASTERED",
                confidence_score=0.9
            )
        ],
        review_updates=[]
    )
    
    recs = rules.generate(outcome)
    assert len(recs) == 1
    assert recs[0].recommended_session_type == "CHALLENGE"
    assert recs[0].priority == 50

def test_learning_path_engine():
    engine = LearningPathEngine(uow=None) # Mocking UoW since we don't need it for pure rules here
    rules = RecommendationRules()
    
    outcome = get_mock_outcome(
        mastery_updates=[
            MasteryUpdatePayload(
                concept_id=uuid.uuid4(),
                old_mastery=0.5,
                new_mastery=0.2, 
                old_status="LEARNING",
                new_status="NEW",
                confidence_score=0.1
            )
        ],
        review_updates=[]
    )
    
    recs = rules.generate(outcome)
    path = engine.generate_path(uuid.uuid4(), recs)
    
    assert path[0] == "PREREQUISITE_REVISION"
    assert path[1] == "RECOVERY"

def test_adaptive_session_selector():
    selector = AdaptiveSessionSelector()
    rules = RecommendationRules()
    
    outcome = get_mock_outcome(
        mastery_updates=[
            MasteryUpdatePayload(
                concept_id=uuid.uuid4(),
                old_mastery=0.5,
                new_mastery=0.2, 
                old_status="LEARNING",
                new_status="NEW",
                confidence_score=0.1
            )
        ],
        review_updates=[]
    )
    
    recs = rules.generate(outcome)
    next_session = selector.select_next_session(uuid.uuid4(), recs)
    
    assert next_session.session_type == "RECOVERY"
