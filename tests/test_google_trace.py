import pytest
import os
import pandas as pd
from src.workload.trace_adapter import GoogleClusterTraceAdapter
from app.services.trace_replay import trace_replay_service

@pytest.fixture
def sample_trace_path():
    path = "data/raw/google_cluster_trace/sample_task_usage.csv"
    if not os.path.exists(path):
        import generate_trace_sample
        os.makedirs(os.path.dirname(path), exist_ok=True)
        generate_trace_sample.generate_sample(path, 10)
    return path

def test_trace_adapter_load_and_normalize(sample_trace_path):
    adapter = GoogleClusterTraceAdapter(sample_trace_path, window_seconds=60)
    df = adapter.load_and_normalize()
    
    assert not df.empty
    # Check normalized columns exist
    assert 'timestamp' in df.columns
    assert 'cpu' in df.columns
    assert 'memory' in df.columns
    assert 'requests' in df.columns
    assert 'network' in df.columns
    assert 'latency' in df.columns
    
    # Check bounds
    assert (df['cpu'] >= 0).all() and (df['cpu'] <= 100).all()
    assert (df['memory'] >= 0).all() and (df['memory'] <= 100).all()

def test_trace_replay_load(sample_trace_path):
    res = trace_replay_service.load_trace(sample_trace_path, 60)
    assert res['loaded'] is True
    assert res['records'] > 0
    
    status = trace_replay_service.get_status()
    assert status['current_position'] == 0
    assert status['is_replaying'] is False

def test_trace_replay_step():
    # Make sure it's loaded
    assert trace_replay_service.trace_df is not None
    
    initial_pos = trace_replay_service.current_index
    trace_replay_service.step_replay()
    
    assert trace_replay_service.current_index == initial_pos + 1
    status = trace_replay_service.get_status()
    assert status['current_workload'] is not None
    assert 'cpu' in status['current_workload']

