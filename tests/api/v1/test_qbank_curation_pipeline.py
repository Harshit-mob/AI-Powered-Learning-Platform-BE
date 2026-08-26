import pytest
import uuid
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.dependencies import get_current_student, get_current_admin, get_uow
from app.models.quiz import QuestionBank, DraftQuestion, Question
from app.models.core.student import Student

client = TestClient(app)

# Create a mock student with ADMIN role to bypass authorization checks
mock_student = Student(
    id=uuid.uuid4(),
    name="Test User",
    grade_id=uuid.uuid4(),
    email="test@curation.com",
    hashed_password="mocked_password",
    role="ADMIN"
)

def override_get_current_user():
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
    app.dependency_overrides[get_current_student] = override_get_current_user
    app.dependency_overrides[get_current_admin] = override_get_current_user
    app.dependency_overrides[get_uow] = lambda: mock_uow
    yield
    app.dependency_overrides.clear()

def test_upload_endpoint_triggers_background_task(mock_uow):
    from app.models.course import Board, Grade, Subject, Chapter
    
    # Mocking board, grade, subject, chapter objects
    mock_board = Board(id=uuid.uuid4(), name="CBSE")
    mock_grade = Grade(id=uuid.uuid4(), name="6", board_id=mock_board.id)
    mock_subject = Subject(id=uuid.uuid4(), name="Science", grade_id=mock_grade.id)
    mock_chapter = Chapter(id=uuid.uuid4(), title="Exploring Magnets", subject_id=mock_subject.id)
    
    # Configure mock_uow queries for dynamic Subject/Chapter resolution
    mock_uow.session.query().filter().first.side_effect = [
        mock_board, mock_grade, mock_subject, mock_chapter
    ]
    
    # Mock form upload file
    file_content = b"%PDF-1.4 mock pdf content"
    files = {"file": ("test_chapter.pdf", file_content, "application/pdf")}
    data = {
        "board_id": str(mock_board.id),
        "grade_id": str(mock_grade.id),
        "subject_id": str(mock_subject.id),
        "chapter_name": "Exploring Magnets"
    }
    
    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
        response = client.post("/api/v1/content/curriculum/qbank/upload", data=data, files=files)
        
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["success"] is True
        assert "qbank_id" in res_json["data"]
        
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

def test_review_updates_draft_status_only(mock_uow):
    qbank_id = uuid.uuid4()
    mock_qbank = QuestionBank(id=qbank_id)
    
    # Mock finding QBank
    mock_uow.session.query().filter().first.return_value = mock_qbank
    
    payload = {
        "approved_ids": [str(uuid.uuid4())],
        "rejected_ids": [str(uuid.uuid4())]
    }
    
    response = client.post(f"/api/v1/content/curriculum/qbank/{qbank_id}/review", json=payload)
    assert response.status_code == 200
    
    # Ensure draft statuses are updated in DB
    assert mock_uow.session.query().filter().update.call_count > 0

def test_toggle_active_fails_under_10_approved(mock_uow):
    qbank_id = uuid.uuid4()
    mock_qbank = QuestionBank(id=qbank_id)
    
    # Mock finding QBank, and count returning 5
    mock_uow.session.query().filter().first.return_value = mock_qbank
    mock_uow.session.query().filter().count.return_value = 5
    
    payload = {"is_active": True}
    response = client.post(f"/api/v1/content/curriculum/qbank/{qbank_id}/toggle-active", json=payload)
    assert response.status_code == 400
    assert "at least 10 approved questions" in response.json()["message"]

def test_delete_qbank(mock_uow):
    qbank_id = uuid.uuid4()
    mock_qbank = QuestionBank(id=qbank_id)
    mock_uow.session.query().filter().first.return_value = mock_qbank
    
    response = client.delete(f"/api/v1/content/curriculum/qbank/{qbank_id}")
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert "removed successfully" in res_json["message"]
    
    mock_uow.session.delete.assert_called_once_with(mock_qbank)

