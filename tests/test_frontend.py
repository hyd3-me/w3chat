from fastapi.testclient import TestClient
from app.main import app

def test_index_page_accessible(client):
    """Test that the main page is accessible at /."""
    response = client.get("/")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

def test_index_page_has_title(client):
    """Test that the main page contains 'w3chat' title."""
    response = client.get("/")
    assert "w3chat" in response.text, "Expected 'w3chat' in response text"

def test_index_page_has_header(client):
    """Test that the main page contains a header element."""
    response = client.get("/")
    assert "<header>" in response.text, "Expected header element in response"

def test_index_page_has_connect_wallet_button(client):
    """Test that the main page contains 'Connect Wallet' button."""
    response = client.get("/")
    assert "Connect Wallet" in response.text, "Expected 'Connect Wallet' button in response"

def test_index_page_has_placeholder(client):
    """Test that the main page contains placeholder for unauthenticated users."""
    response = client.get("/")
    assert "Please connect your wallet to start chatting" in response.text, "Expected placeholder text in response"