from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_workload_analysis_endpoint():
    response = client.post('/api/workload/analyze', json={'source': 'Banking', 'seed': 5})
    assert response.status_code == 200

def test_workload_upload_invalid_extension():
    response = client.post('/api/workload/upload', files={'file': ('bad.txt', b'a,b\n1,2\n', 'text/plain')})
    assert response.status_code == 400

def test_cloud_dry_run():
    response = client.post('/api/cloud/scale?mode=aws', json={'desired_capacity': 4, 'dry_run': True})
    assert response.status_code == 200

def test_csv_upload_valid():
    csv_content = b'timestamp,cpu,memory,network,requests,latency\n2026-10-07 09:00:00,0.32,0.40,0.22,45,61\n2026-10-07 09:05:00,0.34,0.41,0.24,48,62\n'
    response = client.post('/api/workload/upload', files={'file': ('test.csv', csv_content, 'text/csv')})
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'uploaded'
    assert data['result']['row_count'] == 2
    assert 'prediction_error' in data['result']

def test_csv_upload_missing_column():
    csv_content = b'timestamp,cpu,memory,network,requests\n2026-10-07 09:00:00,0.32,0.40,0.22,45\n'
    response = client.post('/api/workload/upload', files={'file': ('missing.csv', csv_content, 'text/csv')})
    assert response.status_code == 400
    assert 'Missing required columns' in response.json()['detail']

def test_csv_upload_invalid_numeric():
    csv_content = b'timestamp,cpu,memory,network,requests,latency\n2026-10-07 09:00:00,invalid,0.40,0.22,45,61\n'
    response = client.post('/api/workload/upload', files={'file': ('invalid.csv', csv_content, 'text/csv')})
    assert response.status_code == 400
    assert 'invalid numeric values' in response.json()['detail'].lower()

def test_csv_upload_empty():
    response = client.post('/api/workload/upload', files={'file': ('empty.csv', b'', 'text/csv')})
    assert response.status_code == 400

def test_csv_upload_valid_full():
    try:
        with open('test.csv', 'rb') as f:
            content = f.read()
    except FileNotFoundError:
        return
        content = f.read()
    response = client.post('/api/workload/upload', files={'file': ('test_full.csv', content, 'text/csv')})
    assert response.status_code == 200
    assert response.json()['result']['row_count'] == 20
    assert 'prediction' in response.json()['result']