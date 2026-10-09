import numpy as np

def schedule_objective(allocation, task_lengths, vm_mips, vm_caps=None):
    a=np.asarray(allocation,dtype=int); lengths=np.asarray(task_lengths,float); m=len(vm_mips); loads=np.zeros(m)
    for i,v in enumerate(a): loads[v % m]+=lengths[i]/max(vm_mips[v % m],1e-9)
    makespan=float(loads.max()); imbalance=float(loads.std()); violation=0.0
    if vm_caps is not None: violation=float(np.maximum(loads-np.asarray(vm_caps),0).sum())
    return makespan + 0.25*imbalance + 10*violation

def minimization_fitness(solution, objective): return float(objective(solution))
