from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def small_payload():
    return {'tasks': 6, 'vms': 3, 'seed': 7, 'population_size': 6, 'iterations': 2}


def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'healthy'}


def test_experiment_endpoint():
    response = client.post('/api/experiments/run', json={'algorithm': 'psoga', **small_payload()})
    assert response.status_code == 200
    data = response.json()
    assert data['algorithm'] == 'psoga'
    assert data['seed'] == 7
    assert 'makespan' in data and 'fitness' in data


def test_optimizer_endpoints():
    for algorithm in ('ga', 'pso', 'psoga'):
        response = client.post(f'/api/optimization/{algorithm}', json=small_payload())
        assert response.status_code == 200
        assert response.json()['algorithm'] == algorithm
