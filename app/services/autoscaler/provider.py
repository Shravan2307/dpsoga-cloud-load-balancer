from abc import ABC, abstractmethod
from typing import List, Dict
import asyncio
from datetime import datetime, timezone
from app.services.autoscaler.models import VM, VMState

class VMProvider(ABC):
    @abstractmethod
    def create_vms(self, count: int) -> List[VM]:
        pass

    @abstractmethod
    def terminate_vms(self, vm_ids: List[str]) -> None:
        pass

    @abstractmethod
    def get_vms(self) -> List[VM]:
        pass

class SimulatedVMProvider(VMProvider):
    def __init__(self):
        self._vms: Dict[str, VM] = {}

    def create_vms(self, count: int) -> List[VM]:
        new_vms = []
        for _ in range(count):
            vm = VM(state=VMState.PROVISIONING)
            self._vms[vm.id] = vm
            new_vms.append(vm)
            
            # Start background task to simulate startup delay if loop is running
            try:
                asyncio.get_running_loop()
                asyncio.create_task(self._simulate_startup(vm.id))
            except RuntimeError:
                # No running event loop, immediately set to RUNNING for simplicity or test sync
                vm.state = VMState.RUNNING
                vm.launched_at = datetime.now(timezone.utc)
                
        return new_vms

    def terminate_vms(self, vm_ids: List[str]) -> None:
        for vid in vm_ids:
            if vid in self._vms and self._vms[vid].state not in (VMState.TERMINATED, VMState.DRAINING):
                self._vms[vid].state = VMState.DRAINING
                try:
                    asyncio.get_running_loop()
                    asyncio.create_task(self._simulate_shutdown(vid))
                except RuntimeError:
                    self._vms[vid].state = VMState.TERMINATED
                    self._vms[vid].terminated_at = datetime.now(timezone.utc)

    def get_vms(self) -> List[VM]:
        return list(self._vms.values())

    async def _simulate_startup(self, vm_id: str):
        await asyncio.sleep(2.0)
        if vm_id in self._vms and self._vms[vm_id].state == VMState.PROVISIONING:
            self._vms[vm_id].state = VMState.RUNNING
            self._vms[vm_id].launched_at = datetime.now(timezone.utc)

    async def _simulate_shutdown(self, vm_id: str):
        await asyncio.sleep(2.0)
        if vm_id in self._vms and self._vms[vm_id].state == VMState.DRAINING:
            self._vms[vm_id].state = VMState.TERMINATED
            self._vms[vm_id].terminated_at = datetime.now(timezone.utc)
