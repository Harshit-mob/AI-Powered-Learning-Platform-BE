import pytest
import uuid
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.dependencies import get_current_admin, get_uow
from app.models.course import Chapter, Topic, Subtopic, LearningUnit
from app.models.core.student import Student

client = TestClient(app)

mock_admin = Student(
    id=uuid.uuid4(),
    name="Test Admin",
    grade_id=uuid.uuid4(),
    email="admin@curation.com",
    role="ADMIN"
)

def override_get_current_admin():
    return mock_admin

@pytest.fixture
def mock_uow():
    uow = MagicMock()
    session = MagicMock()
    uow.session = session
    return uow

@pytest.fixture(autouse=True)
def setup_dependencies(mock_uow):
    app.dependency_overrides[get_current_admin] = override_get_current_admin
    app.dependency_overrides[get_uow] = lambda: mock_uow
    yield
    app.dependency_overrides.clear()

def test_create_topic_manually_success(mock_uow):
    mock_chapter = Chapter(id=uuid.uuid4(), title="Test Chapter", subject_id=uuid.uuid4())
    mock_uow.session.query().filter().first.return_value = mock_chapter
    
    payload = {
        "title": "New Topic",
        "chapter_id": str(mock_chapter.id)
    }
    
    response = client.post("/api/v1/content/curriculum/topics", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "topic_id" in response.json()["data"]

def test_create_question_manually_mcq_success(mock_uow):
    mock_topic = Topic(id=uuid.uuid4(), title="Test Topic", chapter_id=uuid.uuid4())
    mock_uow.session.query().filter().first.return_value = mock_topic
    
    # Mocking first query for Topic, then query for Subtopic (None), then query for LearningUnit (None)
    mock_uow.session.query().filter().first.side_effect = [
        mock_topic, # Topic check
        None,       # Subtopic check
        None,       # LearningUnit check
        None,       # Duplicate Active Question check
        None,       # Duplicate Draft Question check
        None        # QBank check
    ]
    
    payload = {
        "topic_id": str(mock_topic.id),
        "text": "New manual MCQ question",
        "mcq_options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_option": "Option B",
        "expected_answer": "Option B"
    }
    
    response = client.post("/api/v1/content/curriculum/questions", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "question_id" in response.json()["data"]

def test_create_question_manually_validation_fails(mock_uow):
    mock_topic = Topic(id=uuid.uuid4(), title="Test Topic", chapter_id=uuid.uuid4())
    mock_uow.session.query().filter().first.side_effect = [
        mock_topic,
        None,
        None,
        None,
        None,
        None
    ]
    
    payload = {
        "topic_id": str(mock_topic.id),
        "text": "New manual MCQ question",
        "mcq_options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_option": "Option E", # invalid option
        "expected_answer": "Option E"
    }
    
    response = client.post("/api/v1/content/curriculum/questions", json=payload)
    assert response.status_code == 400
    assert "correct_option must match" in response.json()["message"]
