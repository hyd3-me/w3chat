from fastapi.testclient import TestClient
from app.main import app

def test_index_page_accessible(client):
    """Test that the main page is accessible at / and contains expected content."""
    response = client.get("/")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert "w3chat" in response.text, "Expected 'w3chat' in response text"