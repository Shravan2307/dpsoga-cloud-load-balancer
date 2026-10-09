import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_benchmark_api_exists():
    """Verify the benchmark endpoint is registered and accepts requests."""
    response = client.post("/api/benchmark/google-trace/run", json={
        "dataset": "data/raw/google_cluster_trace/sample_task_usage.csv",
        "window_seconds": 60,
        "algorithms": ["ga", "pso"],
        "max_records": 5,
        "seed": 42
    })
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "results" in data
    assert "summary" in data
    
    assert "ga" in data["results"]
    assert "pso" in data["results"]
    
    # Metadata should correctly identify synthetic data
    assert data["metadata"]["data_type"] == "SYNTHETIC"
    
    # Check that summary metrics are calculated
    assert "Cost" in data["summary"]["ga"]
    assert "SLA Violations" in data["summary"]["ga"]

def test_benchmark_api_invalid_file():
    """Verify the benchmark endpoint handles invalid files properly."""
    response = client.post("/api/benchmark/google-trace/run", json={
        "dataset": "data/raw/invalid_file_does_not_exist.csv",
        "window_seconds": 60,
        "algorithms": ["ga"],
        "max_records": 5,
        "seed": 42
    })
    assert response.status_code == 400

