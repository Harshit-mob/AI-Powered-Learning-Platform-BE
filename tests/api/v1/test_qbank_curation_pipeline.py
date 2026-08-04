import pytest
import uuid
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.dependencies import get_current_student, get_uow
from app.models.quiz import QuestionBank, DraftQuestion, Question
from app.models.core.student import Student

client = TestClient(app)

# Create a mock student to bypass authentication
mock_student = Student(
    id=uuid.uuid4(),
    name="Test User",
    grade_id=uuid.uuid4(),
    email="test@curation.com",
    hashed_password="mocked_password"
)

def override_get_current_student():
    return mock_student

@pytest.fixture
def mock_uow():
    uow = MagicMock()
    # Mock database session queries
    session = MagicMock()
    uow.session = session
    return uow

@pytest.fixture(autouse=True)
def setup_dependencies(mock_uow):
    app.dependency_overrides[get_current_student] = override_get_current_student
    app.dependency_overrides[get_uow] = lambda: mock_uow
    yield
    app.dependency_overrides.clear()

def test_upload_endpoint_triggers_background_task(mock_uow):
    subject_id = uuid.uuid4()
    chapter_id = uuid.uuid4()
    
    # Mock form upload file
    file_content = b"%PDF-1.4 mock pdf content"
    files = {"file": ("test_chapter.pdf", file_content, "application/pdf")}
    data = {
        "subject_id": str(subject_id),
        "chapter_id": str(chapter_id),
        "source_type": "TEXTBOOK_EXERCISE"
    }
    
    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
        response = client.post("/api/v1/content/curriculum/qbank/upload", data=data, files=files)
        
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        assert "qbank_id" in res_json["data"]
        
        # Verify QuestionBank added to session
        mock_uow.session.add.assert_called_once()
        added_obj = mock_uow.session.add.call_args[0][0]
        assert isinstance(added_obj, QuestionBank)
        assert added_obj.subject_id == subject_id
        assert added_obj.chapter_id == chapter_id
        
        # Verify background task registered
        mock_add_task.assert_called_once()

def test_get_qbanks_list(mock_uow):
    mock_qbank_row = MagicMock()
    mock_qbank_row.id = uuid.uuid4()
    mock_qbank_row.file_name = "test.pdf"
    mock_qbank_row.source_type = "TEXTBOOK_EXERCISE"
    mock_qbank_row.status = "PROCESSING"
    mock_qbank_row.total_questions = 0
    mock_qbank_row.error_message = None
    import datetime
    mock_qbank_row.created_at = datetime.datetime.now()
    mock_qbank_row.subject_name = "Science"
    mock_qbank_row.chapter_title = "Exploring Magnets"

    mock_uow.session.query().join().join().order_by().all.return_value = [mock_qbank_row]

    response = client.get("/api/v1/content/curriculum/qbank")
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert len(res_json["data"]) == 1
    assert res_json["data"][0]["status"] == "PROCESSING"

def test_toggle_active_status(mock_uow):
    qbank_id = uuid.uuid4()
    
    # Mock finding QuestionBank
    mock_qbank = QuestionBank(id=qbank_id)
    mock_uow.session.query().filter().first.return_value = mock_qbank
    
    payload = {"is_active": False}
    response = client.post(f"/api/v1/content/curriculum/qbank/{qbank_id}/toggle-active", json=payload)
    
    assert response.status_code == 200
    res_json = response.json()
    assert "deactivated" in res_json["message"]
    
    # Verify UPDATE query called on Question model
    mock_uow.session.query().filter().update.assert_called_once_with({"is_active": False}, synchronize_session=False)
