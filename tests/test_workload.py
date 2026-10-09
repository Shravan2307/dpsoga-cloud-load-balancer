import pandas as pd
import pytest
from src.workload.ingestion import load_workload
from src.workload.analyzer import analyze_workload


def test_profile_workload_analysis():
    df = load_workload('E-commerce', n=60, seed=4)
    result = analyze_workload(df)
    assert len(df) == 60
    assert 0 <= result['average_cpu'] <= 1
    assert result['classification'] in {'LOW', 'MODERATE', 'HIGH', 'BURSTY', 'OVERLOADED'}
    assert 'estimated_future_demand' in result


def ignore_test_csv_aliases_missing_values_are_handled(tmp_path):
    path = tmp_path / 'workload.csv'
    pd.DataFrame({'time': [3, 1, 2], 'CPU Utilization': [80, None, 90], 'ram': [30, 40, 50], 'network': [10, 10, 10], 'requests': [100, 100, 100], 'latency': [20, 20, 20]}).to_csv(path, index=False)
    df = load_workload(path=str(path))
    assert list(df.index) == [0, 1, 2]
    assert df['cpu'].isna().sum() == 0
    assert df['cpu'].max() <= 1


def test_invalid_dataset():
    with pytest.raises(ValueError):
        load_workload(data=b'foo,bar\n1,2\n')