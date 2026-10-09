from src.resource_monitor.utilization import ResourceVector,integrated_utilization
def can_host(host,vm): return host.used_cpu()+vm.mips<=host.cpu_mips and host.used_ram()+vm.ram<=host.ram and host.used_storage()+vm.storage<=host.storage and host.used_bandwidth()+vm.bandwidth<=host.bandwidth
def allocate_vm(vm,hosts):
    candidates=[h for h in hosts if can_host(h,vm)]
    if not candidates:return None
    h=min(candidates,key=lambda x: integrated_utilization(ResourceVector((x.used_cpu()+vm.mips)/x.cpu_mips,(x.used_ram()+vm.ram)/x.ram,(x.used_storage()+vm.storage)/x.storage,(x.used_bandwidth()+vm.bandwidth)/x.bandwidth)))
    h.vms.append(vm);vm.host_id=h.id;return h
