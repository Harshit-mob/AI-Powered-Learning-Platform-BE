import pytest
import uuid
from typing import List, Dict, Any

from app.runtime.session.session_types import SessionType
from app.runtime.session.session_config import SessionConfig
from app.runtime.session.distribution_engine import DistributionEngine
from app.runtime.session.chapter_progress_service import ChapterProgressService
from app.runtime.session.exceptions import ChapterNotReadyForRevisionError

class MockQuestion:
    def __init__(self, bloom_taxonomy, difficulty_level):
        self.bloom_taxonomy = bloom_taxonomy
        self.difficulty_level = difficulty_level

def test_distribution_engine_dynamic_sizing():
    engine = DistributionEngine()
    
    # 10 minutes, 60s per question -> 10 questions
    count1 = engine.determine_question_count(10, 60)
    assert count1 == 10
    
    # 15 minutes, 40s per question -> 22 questions (floor)
    count2 = engine.determine_question_count(15, 40)
    assert count2 == 22
    
def test_distribution_engine_policy_enforcement():
    engine = DistributionEngine()
    
    # Create 20 mock candidates (All recall/easy just to see if fallback picks them)
    candidates = [MockQuestion("RECALL", "EASY") for _ in range(20)]
    
    policy = {
        "bloom_distribution": {"RECALL": 0.5, "APPLICATION": 0.5},
        "difficulty_distribution": {"EASY": 1.0}
    }
    
    # It should pick exactly target_count even if exact buckets aren't full (fallback loop)
    selected = engine.apply_policy(candidates, target_count=10, policy=policy)
    assert len(selected) == 10

def test_chapter_revision_unlock():
    class MockUoW:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    # For MVP mock, it always returns True currently, but let's test the interface exists
    service = ChapterProgressService(MockUoW())
    assert service.is_revision_eligible(uuid.uuid4(), uuid.uuid4()) is True
