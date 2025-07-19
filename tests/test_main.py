import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Web3 Chat API"}