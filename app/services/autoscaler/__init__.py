from app.services.autoscaler.models import VM, VMState, ScalingEvent, ScalingAction
from app.services.autoscaler.provider import VMProvider, SimulatedVMProvider
from app.services.autoscaler.service import Autoscaler

__all__ = [
    'VM', 'VMState', 'ScalingEvent', 'ScalingAction',
    'VMProvider', 'SimulatedVMProvider', 'Autoscaler'
]

from app.core.config import settings

# Singleton instances for local app
_provider = SimulatedVMProvider()
autoscaler = Autoscaler(_provider, min_capacity=settings.min_capacity, max_capacity=settings.max_capacity, cooldown_seconds=settings.cooldown_seconds)

# Initialize with initial VMs so the system has some capacity initially
if not _provider.get_vms():
    _provider.create_vms(3)

