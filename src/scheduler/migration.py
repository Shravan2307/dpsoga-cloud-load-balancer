from dataclasses import dataclass
from .vm_allocator import can_host
from .host_selector import select_underloaded,host_score
@dataclass
class MigrationEvent: vm_id:int; source_host:int; destination_host:int; migration_time:float
def migrate_one(overloaded,hosts,bandwidth_rate=1000):
    if not overloaded.vms:return None
    destination=select_underloaded(hosts,overloaded)
    candidates=sorted(overloaded.vms,key=lambda v:(v.ram+v.storage/1000+v.bandwidth/100),reverse=False)
    for vm in candidates:
        if destination and can_host(destination,vm):
            overloaded.vms.remove(vm);destination.vms.append(vm);vm.host_id=destination.id
            return MigrationEvent(vm.id,overloaded.id,destination.id,float((vm.ram+vm.storage/1000)/max(bandwidth_rate,1)))
    return None
