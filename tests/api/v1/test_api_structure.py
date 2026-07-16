import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_missing_auth_returns_403():
    # Attempt to hit protected endpoint without token
    response = client.get("/api/v1/student/profile")
    assert response.status_code == 403
    
def test_unsupported_route_returns_404():
    response = client.get("/api/v1/does_not_exist")
    assert response.status_code == 404

# In a real environment we'd mock the UnitOfWork and Database for full end-to-end integration tests here.
