import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import numpy as np
from src.optimization.ga import GeneticAlgorithm
from src.optimization.pso import ParticleSwarmOptimizer
from src.optimization.hybrid_psoga import HybridPSOGA
from src.resource_monitor.utilization import ResourceVector,integrated_utilization
from src.resource_monitor.machine_classifier import classify_machine
from src.simulation.entities import Host,VM
from src.scheduler.vm_allocator import allocate_vm
from src.scheduler.migration import migrate_one

def test_optimizers():
 f=lambda x: float(np.sum(np.asarray(x)**2));
 for C in [GeneticAlgorithm,ParticleSwarmOptimizer,HybridPSOGA]:
  r=C(f,5,4,population_size=8,iterations=3,seed=1).run();assert len(r.best_solution)==5;assert len(r.history)==3

def test_resources_and_classifier():
 assert integrated_utilization(ResourceVector(0,0,0,0))==0;assert classify_machine(.9)=='OL';assert classify_machine(0)=='FH'

def test_allocation_and_migration():
 hs=[Host(0,cpu_mips=1000,ram=2000,storage=30000,bandwidth=1000),Host(1,cpu_mips=1000,ram=4000,storage=30000,bandwidth=2000)];v=VM(1,mips=400,ram=500,bandwidth=200);v2=VM(2,mips=400,ram=500,bandwidth=200);hs[0].vms.extend([v,v2]);e=migrate_one(hs[0],hs);assert e and e.destination_host==1

def test_model_forward():
 import torch
 from src.models.cnn_lstm import CNNLSTM
 m=CNNLSTM(5,filters=8,hidden_units=8,output_size=5);assert m(torch.randn(2,5,5)).shape==(2,5)
