import pytest
import time
import asyncio
from app.services.autoscaler.models import VMState, ScalingAction
from app.services.autoscaler.provider import SimulatedVMProvider
from app.services.autoscaler.service import Autoscaler

@pytest.fixture
def provider():
    return SimulatedVMProvider()

@pytest.fixture
def autoscaler(provider):
    return Autoscaler(provider, min_capacity=1, max_capacity=20, cooldown_seconds=0)

def test_initial_provider_empty(provider):
    assert len(provider.get_vms()) == 0

@pytest.mark.asyncio
async def test_provider_create_vms(provider):
    vms = provider.create_vms(2)
    assert len(vms) == 2
    assert vms[0].state == VMState.PROVISIONING

@pytest.mark.asyncio
async def test_provider_simulate_startup():
    provider = SimulatedVMProvider()
    vms = provider.create_vms(1)
    assert vms[0].state == VMState.PROVISIONING
    
    # Wait for the startup task to complete
    await asyncio.sleep(2.5)
    
    # After simulation
    assert vms[0].state == VMState.RUNNING

@pytest.mark.asyncio
async def test_provider_simulate_shutdown():
    provider = SimulatedVMProvider()
    vms = provider.create_vms(1)
    await asyncio.sleep(2.5)
    assert vms[0].state == VMState.RUNNING
    
    provider.terminate_vms([vms[0].id])
    assert vms[0].state == VMState.DRAINING
    
    await asyncio.sleep(2.5)
    assert vms[0].state == VMState.TERMINATED

def test_autoscaler_scale_out(autoscaler):
    event = autoscaler.evaluate(3)
    assert event.action == ScalingAction.SCALE_OUT
    assert event.vms_before == 0
    assert event.vms_after == 3
    
    status = autoscaler.get_status()
    assert status['total'] == 3
    assert status['active'] == 3

def test_autoscaler_scale_in(autoscaler):
    autoscaler.evaluate(4)
    assert autoscaler.get_status()['active'] == 4
    
    event = autoscaler.evaluate(2)
    assert event.action == ScalingAction.SCALE_IN
    assert event.vms_before == 4
    assert event.vms_after == 2
    assert autoscaler.get_status()['active'] == 2
    
def test_autoscaler_cooldown(provider):
    scaler = Autoscaler(provider, cooldown_seconds=10)
    scaler.evaluate(3) # Initial scale out
    
    # Immediate second evaluation should be ignored due to cooldown
    event = scaler.evaluate(5)
    assert event.action == ScalingAction.MAINTAIN
    assert event.target_vms == 5
    assert event.vms_after == 3

def test_autoscaler_min_max_limits(autoscaler):
    # Test max limit
    event = autoscaler.evaluate(25)
    assert event.action == ScalingAction.SCALE_OUT
    assert event.vms_after == 20
    
    # Test min limit
    event = autoscaler.evaluate(0)
    assert event.action == ScalingAction.SCALE_IN
    assert event.vms_after == 1
