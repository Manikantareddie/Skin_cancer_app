import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


def test_model_status():
    response = client.get("/api/v1/model/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_loaded" in data
    assert "architecture" in data
    assert data["classes"] == ["Benign", "Malignant"]
