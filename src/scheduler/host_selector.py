from src.resource_monitor.utilization import ResourceVector,integrated_utilization
def host_score(host): return integrated_utilization(ResourceVector(host.used_cpu()/host.cpu_mips,host.used_ram()/host.ram,host.used_storage()/host.storage,host.used_bandwidth()/host.bandwidth))
def select_underloaded(hosts,exclude=None): return min([h for h in hosts if h is not exclude],key=host_score,default=None)
