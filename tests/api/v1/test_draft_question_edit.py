import pytest
import uuid
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.dependencies import get_current_admin, get_uow
from app.models.quiz import DraftQuestion
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

def test_update_draft_question_mcq_success(mock_uow):
    mock_draft = DraftQuestion(
        id=uuid.uuid4(),
        question_type="MCQ",
        text="Old question",
        mcq_options=["A", "B", "C", "D"],
        correct_option="A",
        expected_answer="A",
        acceptable_answers=["A"],
        difficulty=2
    )
    mock_uow.session.query().filter().first.return_value = mock_draft
    
    payload = {
        "text": "New MCQ question",
        "mcq_options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_option": "Option B",
        "expected_answer": "Option B"
    }
    
    response = client.put(f"/api/v1/content/curriculum/qbank/draft-questions/{mock_draft.id}", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert mock_draft.text == "New MCQ question"
    assert mock_draft.correct_option == "Option B"
    assert mock_draft.mcq_options == ["Option A", "Option B", "Option C", "Option D"]

def test_update_draft_question_validation_fails(mock_uow):
    mock_draft = DraftQuestion(
        id=uuid.uuid4(),
        question_type="MCQ",
        text="Old question",
        mcq_options=["A", "B", "C", "D"],
        correct_option="A",
        expected_answer="A"
    )
    mock_uow.session.query().filter().first.return_value = mock_draft
    
    payload = {
        "correct_option": "E"
    }
    response = client.put(f"/api/v1/content/curriculum/qbank/draft-questions/{mock_draft.id}", json=payload)
    assert response.status_code == 400
    assert "correct_option must match" in response.json()["message"]
