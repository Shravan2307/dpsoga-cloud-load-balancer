from .utilization import ResourceVector, integrated_utilization
def calculate_resource_score(cpu, ram, storage, bandwidth, weights=None):
    return integrated_utilization(ResourceVector(cpu,ram,storage,bandwidth), weights)
