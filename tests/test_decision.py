from src.decision_engine import ResourceDecisionEngine
from app.services.cloud import SimulationAdapter, AWSCloudAdapter


def test_resource_decision_scale_out_and_limits():
    engine = ResourceDecisionEngine(minimum_capacity=1, maximum_capacity=5, safe_utilization=.75)
    result = engine.decide(current_capacity=2, predicted_demand=1.0)
    assert result.action == 'SCALE OUT'
    assert result.recommended_capacity <= 5


def test_simulation_adapter_and_aws_dry_run():
    assert SimulationAdapter().status()['status'] == 'available'
    result = AWSCloudAdapter(dry_run=True).scale(4)
    assert result['dry_run'] is True
    assert 'no AWS infrastructure changed' in result['status']
