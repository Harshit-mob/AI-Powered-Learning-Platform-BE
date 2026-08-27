import pytest
import uuid
from unittest.mock import MagicMock
from app.runtime.session.distribution_policy import QuotaDistributionPolicy
from app.runtime.session.question_variant_selector import VariantScore
from app.models.quiz import Question

def test_quota_distribution_policy_selects_manual_questions():
    # 1. Setup mock questions
    q_manual_1 = Question(
        id=uuid.uuid4(),
        text="Manual Question 1",
        difficulty=2,
        bloom_level="COMPREHENSION",
        source_type="MANUAL"
    )
    q_manual_2 = Question(
        id=uuid.uuid4(),
        text="Manual Question 2",
        difficulty=2,
        bloom_level="COMPREHENSION",
        source_type="MANUAL"
    )
    q_ai_1 = Question(
        id=uuid.uuid4(),
        text="AI Question 1",
        difficulty=1,
        bloom_level="RECALL",
        source_type="AI_GENERATED"
    )
    q_ai_2 = Question(
        id=uuid.uuid4(),
        text="AI Question 2",
        difficulty=1,
        bloom_level="RECALL",
        source_type="AI_GENERATED"
    )

    # 2. Setup mock variant scores
    v_manual_1 = VariantScore(question=q_manual_1, score=1.0, difficulty="MEDIUM", bloom="COMPREHENSION")
    v_manual_2 = VariantScore(question=q_manual_2, score=1.0, difficulty="MEDIUM", bloom="COMPREHENSION")
    v_ai_1 = VariantScore(question=q_ai_1, score=0.9, difficulty="EASY", bloom="RECALL")
    v_ai_2 = VariantScore(question=q_ai_2, score=0.8, difficulty="EASY", bloom="RECALL")

    # 3. Setup LUs
    lu_1 = uuid.uuid4()
    lu_2 = uuid.uuid4()
    
    ranked_lus = [lu_1, lu_2]
    variants_by_lu = {
        lu_1: [v_manual_1, v_ai_1],
        lu_2: [v_manual_2, v_ai_2]
    }

    # 4. Instantiate policy
    policy = QuotaDistributionPolicy(
        target_count=4,
        difficulty_distribution={"EASY": 0.5, "MEDIUM": 0.5, "HARD": 0.0},
        bloom_distribution={"RECALL": 0.5, "COMPREHENSION": 0.5, "APPLICATION": 0.0},
        allow_partial=True
    )

    # 5. Apply policy
    results = policy.apply(ranked_lus, variants_by_lu)
    
    # 6. Verify manual questions are prioritized
    selected_manual_ids = [v.question.id for v in results if v.question.source_type == "MANUAL"]
    assert len(selected_manual_ids) == 2
    assert q_manual_1.id in selected_manual_ids
    assert q_manual_2.id in selected_manual_ids
