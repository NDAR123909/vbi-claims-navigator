"""Tests for API endpoints."""
import pytest
from app.core.config import settings


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "VBI Claims Navigator API"
    assert "version" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_query_endpoint(client):
    """Test query endpoint."""
    response = client.post(
        "/api/v1/query",
        json={"query": "What is PTSD?"},
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "confidence" in data
    assert 0.0 <= data["confidence"] <= 1.0


def test_query_endpoint_missing_api_key(client):
    """Test query endpoint without API key."""
    response = client.post(
        "/api/v1/query",
        json={"query": "test"}
    )
    assert response.status_code == 401


def test_embeddings_endpoint(client):
    """Test embeddings endpoint."""
    response = client.post(
        "/api/v1/embeddings",
        json={"text": "Test text for embedding"},
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert "embedding" in data
    assert isinstance(data["embedding"], list)
    assert len(data["embedding"]) > 0


def test_retrieve_endpoint(client):
    """Test retrieve endpoint."""
    response = client.post(
        "/api/v1/retrieve",
        json={"query": "PTSD claim", "top_k": 5},
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)


def test_draft_endpoint(client, test_client_record):
    """Test draft endpoint."""
    response = client.post(
        "/api/v1/draft",
        json={
            "client_id": test_client_record.id,
            "claim_type": "PTSD",
            "evidence_ids": [1, 2],
            "template": "21-4138_personal_statement"
        },
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert "draft_text" in data
    assert "evidence_map" in data
    assert "human_review_required" in data
    assert data["human_review_required"] is True
    assert "confidence" in data
    assert "next_steps" in data


def test_get_client_endpoint(client, test_client_record):
    """Test get client endpoint."""
    response = client.get(
        f"/api/v1/client/{test_client_record.id}",
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_client_record.id
    assert "client_number" in data


def test_compute_metrics_endpoint(client):
    """Test compute metrics endpoint."""
    response = client.post(
        "/api/v1/compute/metrics",
        json={},
        headers={"X-API-Key": settings.API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_clients" in data
    assert "total_claims" in data
    assert "claims_by_status" in data
    assert "average_confidence_score" in data


def test_plugin_manifest(client):
    """Test ChatGPT plugin manifest."""
    response = client.get("/.well-known/ai-plugin.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name_for_human"] == "VBI Claims Navigator"
    assert "api" in data
    assert "auth" in data

