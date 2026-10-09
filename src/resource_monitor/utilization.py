from dataclasses import dataclass
import numpy as np

@dataclass
class ResourceVector:
    cpu: float
    ram: float
    storage: float
    bandwidth: float
    def clipped(self): return ResourceVector(*[float(np.clip(x,0,1)) for x in (self.cpu,self.ram,self.storage,self.bandwidth)])

def _ratio(used, capacity): return float(np.clip(used / max(capacity, 1e-12), 0, 1))
def calculate_cpu_utilization(used, capacity): return _ratio(used, capacity)
def calculate_ram_utilization(used, capacity): return _ratio(used, capacity)
def calculate_storage_utilization(used, capacity): return _ratio(used, capacity)
def calculate_bandwidth_utilization(used, capacity): return _ratio(used, capacity)
def integrated_utilization(r: ResourceVector, weights=None):
    w=np.asarray(weights if weights is not None else [0.4,0.25,0.15,0.2],float); w=w/w.sum(); return float(np.dot(w, np.asarray([r.cpu,r.ram,r.storage,r.bandwidth])))
