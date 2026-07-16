import pytest
import uuid
from typing import Dict, Any

from app.services.analytics.question.quality_monitor import QuestionQualityMonitor
from app.services.analytics.consumers.event_consumer import AnalyticsDispatcher
from app.models.analytics.question_analytics import QuestionAnalytics

class MockQuestionAnalyticsRepo:
    def __init__(self):
        self.data = {}

    def get_by_question_id(self, q_id):
        return self.data.get(q_id)

    def increment_attempt(self, q_id):
        if q_id not in self.data:
            self.data[q_id] = QuestionAnalytics(question_id=q_id, total_attempts=1, accuracy_rate=0.0)
        else:
            self.data[q_id].total_attempts += 1

    def update_accuracy(self, q_id, acc):
        self.data[q_id].accuracy_rate = acc

class MockUoW:
    def __init__(self):
        self.question_analytics = MockQuestionAnalyticsRepo()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def commit(self): pass

def test_question_quality_monitor_low_accuracy():
    # Setup mock UoW
    uow = MockUoW()
    q_id = uuid.uuid4()
    
    uow.question_analytics.data[q_id] = QuestionAnalytics(
        question_id=q_id,
        total_attempts=55, # > 10
        accuracy_rate=0.10, # < 15%
        skip_rate=0.05
    )
    
    monitor = QuestionQualityMonitor(uow)
    report = monitor.analyze_quality(q_id)
    
    assert report.flagged is True
    assert "Accuracy too low" in report.reason

def test_question_quality_monitor_high_skip():
    uow = MockUoW()
    q_id = uuid.uuid4()
    
    uow.question_analytics.data[q_id] = QuestionAnalytics(
        question_id=q_id,
        total_attempts=20,
        accuracy_rate=0.50,
        skip_rate=0.40 # > 30%
    )
    
    monitor = QuestionQualityMonitor(uow)
    report = monitor.analyze_quality(q_id)
    
    assert report.flagged is True
    assert "Skip rate too high" in report.reason

def test_event_dispatcher_replay():
    # Stub test for the dispatcher logic
    # In a real test, you'd pass a factory that yields a mock UoW and assert calls on the services
    def mock_factory():
        return MockUoW()
        
    dispatcher = AnalyticsDispatcher(mock_factory)
    events = [
        {"event_name": "QuestionAnswered", "payload": {"question_id": uuid.uuid4(), "is_correct": True}}
    ]
    
    # Run replay. If it doesn't crash, the wiring is mostly correct for the test context
    dispatcher.replay_events(events)
    # Passed safely
