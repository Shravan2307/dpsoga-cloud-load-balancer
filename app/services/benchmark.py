import time
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

from src.workload.trace_adapter import GoogleClusterTraceAdapter
from src.simulation.entities import Cloudlet, VM, Host
from src.simulation.simulator import run_algorithm
from app.services.autoscaler import SimulatedVMProvider, Autoscaler
from src.decision_engine import ResourceDecisionEngine

def calculate_sla_violations(cpu_util, memory_util):
    """Simple derived SLA violation penalty (if util > 90%)"""
    violations = 0
    if cpu_util > 0.9:
        violations += (cpu_util - 0.9) * 10
    if memory_util > 0.9:
        violations += (memory_util - 0.9) * 10
    return violations

def calculate_estimated_cost(vms_active, duration_hours):
    """Derived metric for cost estimation based on active VMs"""
    # Assuming $0.05 per VM per hour
    return vms_active * 0.05 * max(duration_hours, 0.1)

def run_benchmark(dataset_path: str, window_seconds: int, algorithms: List[str], seed: int = 42, max_records: int = 100):
    """
    Executes the benchmark across all selected algorithms on a given trace.
    """
    adapter = GoogleClusterTraceAdapter(dataset_path, window_seconds=window_seconds)
    workload_df = adapter.load_and_normalize()
    
    if max_records and len(workload_df) > max_records:
        workload_df = workload_df.head(max_records)
        
    results = {}
    
    for algo in algorithms:
        print(f"Running benchmark for {algo}...")
        
        decision_engine = ResourceDecisionEngine(minimum_capacity=1, maximum_capacity=20, safe_utilization=0.75)
        
        algo_metrics = {
            "vm_count_history": [],
            "cpu_util_history": [],
            "mem_util_history": [],
            "sla_violations": 0,
            "scaling_events": 0,
            "total_execution_time": 0.0,
            "wastage": 0.0,
            "cost": 0.0
        }
        
        start_time = time.perf_counter()
        
        current_vms = 3 # Starting baseline
        
        for _, row in workload_df.iterrows():
            task_count = max(1, int(row.get('requests', 50) / 10))
            
            sim_res = run_algorithm(
                algorithm=algo, 
                num_tasks=task_count, 
                num_vms=current_vms, 
                seed=seed,
                population_size=10,
                iterations=10
            )
            
            cpu_util = sim_res.get('cpu_utilization', 0)
            mem_util = sim_res.get('ram_utilization', 0)
            
            algo_metrics["vm_count_history"].append(current_vms)
            algo_metrics["cpu_util_history"].append(cpu_util)
            algo_metrics["mem_util_history"].append(mem_util)
            
            algo_metrics["sla_violations"] += calculate_sla_violations(cpu_util, mem_util)
            algo_metrics["wastage"] += max(0, (1.0 - cpu_util) * current_vms)
            
            decision = decision_engine.decide(
                current_capacity=current_vms,
                predicted_demand=row['cpu'] / 100.0 * 2
            )
            
            if decision.action != "MAINTAIN":
                algo_metrics["scaling_events"] += 1
                current_vms = decision.recommended_capacity
                
        end_time = time.perf_counter()
        algo_metrics["total_execution_time"] = end_time - start_time
        algo_metrics["cost"] = calculate_estimated_cost(np.mean(algo_metrics["vm_count_history"]), len(workload_df) * window_seconds / 3600.0)
        
        results[algo] = algo_metrics
        
    # Generate summary
    summary = {}
    for algo, m in results.items():
        summary[algo] = {
            "Avg VM": float(np.mean(m["vm_count_history"])),
            "Peak VM": int(np.max(m["vm_count_history"])),
            "CPU Util.": float(np.mean(m["cpu_util_history"])),
            "Memory Util.": float(np.mean(m["mem_util_history"])),
            "SLA Violations": float(m["sla_violations"]),
            "Wastage": float(m["wastage"]),
            "Cost": float(m["cost"]),
            "Execution Time": float(m["total_execution_time"])
        }
        
    return {
        "metadata": {
            "dataset": "Google Cluster Data 2011-2",
            "source": "https://github.com/google/cluster-data",
            "data_type": "REAL" if "sample" not in dataset_path else "SYNTHETIC",
            "window_seconds": window_seconds,
            "records": len(workload_df),
            "seed": seed
        },
        "results": results,
        "summary": summary
    }
