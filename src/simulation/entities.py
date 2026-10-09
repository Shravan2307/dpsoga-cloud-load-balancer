from dataclasses import dataclass,field
@dataclass
class Cloudlet: id:int; length:float; ram:float=256; bandwidth:float=100
@dataclass
class VM: id:int; mips:float=1000; ram:float=1024; storage:float=10000; bandwidth:float=1000; cloudlets:list=field(default_factory=list); host_id:int|None=None
@dataclass
class Host:
 id:int; cpu_mips:float=10000; ram:float=16384; storage:float=100000; bandwidth:float=10000; vms:list=field(default_factory=list); idle_power:float=100; max_power:float=250
 def used_cpu(self): return sum(v.mips for v in self.vms)
 def used_ram(self): return sum(v.ram for v in self.vms)
 def used_storage(self): return sum(v.storage for v in self.vms)
 def used_bandwidth(self): return sum(v.bandwidth for v in self.vms)
@dataclass
class Datacenter: id:int; hosts:list
