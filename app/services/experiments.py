import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.simulation.simulator import run_algorithm


def run_experiment(req):
    result = run_algorithm(
        req.algorithm,
        num_tasks=req.tasks,
        num_vms=req.vms,
        num_datacenters=req.datacenters,
        hosts_per_datacenter=req.hosts_per_datacenter,
        population_size=req.population_size,
        iterations=req.iterations,
        seed=req.seed,
    )
    return {
        'algorithm': req.algorithm,
        'seed': req.seed,
        'makespan': float(result['makespan']),
        'fitness': float(result['best_fitness']),
        'runtime': float(result['running_time']),
        'waiting_time': float(result['average_waiting_time']),
        'response_time': float(result['average_response_time']),
        'migration_count': int(result['migration_count']),
        'migration_time': float(result['migration_time']),
        'energy': float(result['energy_kwh']),
        'cpu_utilization': float(result['cpu_utilization']),
        'ram_utilization': float(result['ram_utilization']),
        'storage_utilization': float(result['storage_utilization']),
        'bandwidth_utilization': float(result['bandwidth_utilization']),
    }


def read_result(filename):
    path = ROOT / 'results' / 'tables' / filename
    if not path.exists():
        return {'status': 'not_available', 'result': {}}
    if path.suffix == '.json':
        return {'status': 'available', 'result': json.loads(path.read_text())}
    import pandas as pd
    return {'status': 'available', 'result': pd.read_csv(path).to_dict(orient='records')}
