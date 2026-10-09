import time
import asyncio
from typing import List, Dict, Any
from app.services.autoscaler.models import VM, VMState, ScalingEvent, ScalingAction
from app.services.autoscaler.provider import VMProvider

class Autoscaler:
    def __init__(self, provider: VMProvider, min_capacity: int = 1, max_capacity: int = 20, cooldown_seconds: int = 300):
        self.provider = provider
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity
        self.cooldown_seconds = cooldown_seconds
        
        self.history: List[ScalingEvent] = []
        self.last_scaling_time = 0.0

    def evaluate(self, target_capacity: int, reason: str = "") -> ScalingEvent:
        now = time.time()
        
        all_vms = self.provider.get_vms()
        active_vms = [vm for vm in all_vms if vm.state in (VMState.PROVISIONING, VMState.RUNNING)]
        current_capacity = len(active_vms)
        
        target_capacity = max(self.min_capacity, min(target_capacity, self.max_capacity))
        
        if target_capacity == current_capacity:
            event = ScalingEvent(
                action=ScalingAction.MAINTAIN,
                reason="Capacity matches target. " + reason,
                vms_before=current_capacity,
                vms_after=current_capacity,
                target_vms=target_capacity
            )
            self.history.append(event)
            return event
            
        if now - self.last_scaling_time < self.cooldown_seconds:
            event = ScalingEvent(
                action=ScalingAction.MAINTAIN,
                reason=f"In cooldown period ({int(self.cooldown_seconds - (now - self.last_scaling_time))}s remaining).",
                vms_before=current_capacity,
                vms_after=current_capacity,
                target_vms=target_capacity
            )
            self.history.append(event)
            return event

        if target_capacity > current_capacity:
            count = target_capacity - current_capacity
            self.provider.create_vms(count)
            event = ScalingEvent(
                action=ScalingAction.SCALE_OUT,
                reason=reason,
                vms_before=current_capacity,
                vms_after=target_capacity,
                target_vms=target_capacity
            )
        else:
            count = current_capacity - target_capacity
            to_terminate = sorted(active_vms, key=lambda v: v.created_at, reverse=True)[:count]
            self.provider.terminate_vms([v.id for v in to_terminate])
            
            event = ScalingEvent(
                action=ScalingAction.SCALE_IN,
                reason=reason,
                vms_before=current_capacity,
                vms_after=target_capacity,
                target_vms=target_capacity
            )

        self.last_scaling_time = now
        self.history.append(event)
        return event

    def get_status(self) -> Dict[str, Any]:
        vms = self.provider.get_vms()
        counts = {state.value: sum(1 for vm in vms if vm.state == state) for state in VMState}
        return {
            "vms": counts,
            "total": len(vms),
            "active": counts.get(VMState.RUNNING.value, 0) + counts.get(VMState.PROVISIONING.value, 0),
            "last_scaling_time": self.last_scaling_time,
            "min_capacity": self.min_capacity,
            "max_capacity": self.max_capacity,
            "cooldown_seconds": self.cooldown_seconds
        }

    async def background_loop(self, interval: int = 10):
        from app.services.automation import _STATE, decide
        while True:
            try:
                # Only scale if we have an analysis and prediction
                if _STATE.get('analysis'):
                    decision = decide()
                    target = decision['recommended_capacity']
                    self.evaluate(target, reason="Background loop tick")
            except Exception as e:
                print(f"Autoscaler loop error: {e}")
            await asyncio.sleep(interval)
