import pytest
import uuid
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.dependencies import get_current_admin, get_uow
from app.models.prompt import SystemPrompt
from app.models.core.student import Student

client = TestClient(app)

mock_admin = Student(
    id=uuid.uuid4(),
    name="Test Admin",
    grade_id=uuid.uuid4(),
    email="admin@curation.com",
    hashed_password="mocked_password",
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

def test_list_prompts(mock_uow):
    mock_prompt = SystemPrompt(name="question_generator", content="Mocked content" * 10)
    mock_uow.session.query().all.return_value = [mock_prompt]
    
    response = client.get("/api/v1/admin/prompts")
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert len(res_json["data"]) == 2
    assert res_json["data"][0]["id"] == "question_generator"
    assert res_json["data"][0]["label"] == "Question Generator"
    


def test_update_prompt(mock_uow):
    mock_prompt = SystemPrompt(name="question_generator", content="Old content" * 10)
    mock_uow.session.query().filter().first.return_value = mock_prompt
    
    payload = {"content": "Updated content " * 10} # 160 characters
    response = client.put("/api/v1/admin/prompts/question_generator", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert mock_prompt.content == ("Updated content " * 10).strip()

def test_update_prompt_validation_fails(mock_uow):
    payload = {"content": "short prompt"}
    response = client.put("/api/v1/admin/prompts/question_generator", json=payload)
    assert response.status_code == 422
