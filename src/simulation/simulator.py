import time, numpy as np
from .entities import Cloudlet,VM,Host,Datacenter
from src.optimization.fitness import schedule_objective
from src.optimization.ga import GeneticAlgorithm
from src.optimization.pso import ParticleSwarmOptimizer
from src.optimization.hybrid_psoga import HybridPSOGA
from src.resource_monitor.utilization import ResourceVector,integrated_utilization
from src.resource_monitor.machine_classifier import classify_machine
from src.scheduler.migration import migrate_one

def build_workload(num_tasks=50,num_vms=12,num_datacenters=3,hosts_per_datacenter=4,seed=42):
 r=np.random.default_rng(seed);tasks=[Cloudlet(i,float(r.integers(500,2501)),float(r.integers(256,1025)),float(r.integers(100,501))) for i in range(num_tasks)];vms=[VM(i,float(r.integers(500,2001)),float(r.integers(250,3001)),10000,float(r.integers(250,1501))) for i in range(num_vms)];hosts=[Host(i) for i in range(num_datacenters*hosts_per_datacenter)];return tasks,vms,hosts

def run_algorithm(algorithm='psoga',num_tasks=50,num_vms=12,seed=42,**kwargs):
 workload_keys={'num_datacenters','hosts_per_datacenter'}
 tasks,vms,hosts=build_workload(num_tasks,num_vms,seed=seed,**{k:v for k,v in kwargs.items() if k in workload_keys}); lengths=[t.length for t in tasks]; mips=[v.mips for v in vms]; objective=lambda a:schedule_objective(a,lengths,mips)
 common=dict(objective=objective,dimensions=num_tasks,upper_bound=num_vms,population_size=kwargs.get('population_size',24),iterations=kwargs.get('iterations',20),seed=seed)
 if algorithm=='ga':opt=GeneticAlgorithm(**common,crossover_rate=.9,mutation_rate=.06)
 elif algorithm=='pso':opt=ParticleSwarmOptimizer(**common)
 else:opt=HybridPSOGA(**common,crossover_rate=.9,mutation_rate=.06)
 start=time.perf_counter();result=opt.run();runtime=time.perf_counter()-start
 for i,v in enumerate(vms):v.cloudlets=[tasks[j] for j,x in enumerate(result.best_solution) if x==i]
 for v in vms:
  if v.cloudlets:
   # first-fit VM placement; unplaceable VMs remain unhosted
   candidates=[h for h in hosts if h.used_cpu()+v.mips<=h.cpu_mips and h.used_ram()+v.ram<=h.ram and h.used_bandwidth()+v.bandwidth<=h.bandwidth]
   if candidates: h=min(candidates,key=lambda x:x.used_cpu()/x.cpu_mips);h.vms.append(v);v.host_id=h.id
 events=[]
 for h in hosts:
  score=integrated_utilization(ResourceVector(h.used_cpu()/h.cpu_mips,h.used_ram()/h.ram,h.used_storage()/h.storage,h.used_bandwidth()/h.bandwidth))
  if classify_machine(score)=='OL':
   e=migrate_one(h,hosts); e and events.append(e)
 makespan=result.best_fitness;loads=np.bincount(result.best_solution,minlength=num_vms);util=float(np.mean(loads/np.maximum(loads.max(),1)))
 energy=sum(h.idle_power+(h.max_power-h.idle_power)*min(1,h.used_cpu()/h.cpu_mips) for h in hosts)*max(makespan,1)/3600
 return {'algorithm':algorithm,'best_fitness':result.best_fitness,'makespan':makespan,'running_time':runtime,'migration_count':len(events),'migration_time':sum(e.migration_time for e in events),'average_waiting_time':float(np.mean(loads)),'average_response_time':float(np.mean(loads)+makespan/2),'energy_kwh':energy,'cpu_utilization':float(np.mean([h.used_cpu()/h.cpu_mips for h in hosts])),'ram_utilization':float(np.mean([h.used_ram()/h.ram for h in hosts])),'storage_utilization':float(np.mean([h.used_storage()/h.storage for h in hosts])),'bandwidth_utilization':float(np.mean([h.used_bandwidth()/h.bandwidth for h in hosts])),'fitness_history':result.history}
