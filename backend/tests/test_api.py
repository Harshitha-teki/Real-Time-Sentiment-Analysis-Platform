import pytest
from fastapi.testclient import TestClient
from main import app  # Import directly for Docker environment

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_posts_structure():
    response = client.get("/api/posts")
    assert response.status_code == 200
    assert "posts" in response.json()

def test_distribution_endpoint():
    response = client.get("/api/sentiment/distribution")
    assert response.status_code == 200