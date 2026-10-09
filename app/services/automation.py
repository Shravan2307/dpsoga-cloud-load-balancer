from __future__ import annotations

import json
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.data.preprocessing import make_sequences, normalize, split
from src.evaluation.metrics import mae
from src.models.cnn_lstm import CNNLSTM, predict, train_model
from src.models.psoga_optimizer import CNNLSTMPSOGA
from src.simulation.simulator import run_algorithm
from src.decision_engine import ResourceDecisionEngine
from src.workload.analyzer import analyze_workload
from src.workload.ingestion import load_workload

from app.core.config import settings

_STATE: dict[str, Any] = {'df': None, 'analysis': None, 'prediction': None, 'comparison': None, 'decision': None, 'current_capacity': 3}


def _jsonable(value):
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def ingest(source='E-commerce', path=None, data=None, seed=None):
    df = load_workload(source=source, path=path, data=data, seed=seed or settings.random_seed)
    analysis = analyze_workload(df)
    _STATE.update(df=df, analysis=analysis)
    return {'analysis': analysis, 'preview': df.head(10).to_dict(orient='records'), 'rows': len(df)}


def latest_dataframe():
    if _STATE.get('df') is None:
        raise ValueError('No workload has been ingested yet.')
    return _STATE['df']


def _prediction(df: pd.DataFrame, seed: int, window: int = 5, epochs: int = 2):
    features = ['cpu', 'memory', 'network', 'requests', 'latency']
    values = df[features].to_numpy(float)
    # Request rate and latency are scaled for a stable shared multi-resource model.
    scales = np.maximum(np.nanmax(values, axis=0), 1e-9)
    normalized = values / scales
    X, y = make_sequences(normalized, window)
    if len(X) < 8:
        raise ValueError('At least 13 workload rows are required for prediction.')
    (x_train, y_train), (x_val, y_val), (x_test, y_test) = split(X, y)
    baseline = CNNLSTM(X.shape[2], filters=8, hidden_units=8, output_size=y.shape[1])
    baseline_loss = train_model(baseline, x_train, y_train, epochs=epochs, lr=0.003, seed=seed)
    baseline_pred = predict(baseline, x_test)
    optimizer = CNNLSTMPSOGA(x_train, y_train, x_val, y_val, seed=seed, population_size=3, iterations=2)
    params, val_mae, history = optimizer.run()
    arch = {k: params[k] for k in ['filters', 'kernel_size', 'pool_size', 'hidden_units', 'layers', 'dropout']}
    model = CNNLSTM(X.shape[2], **arch, output_size=y.shape[1])
    train_model(model, np.concatenate([x_train, x_val]), np.concatenate([y_train, y_val]), epochs=epochs, lr=params['learning_rate'], batch_size=params['batch_size'], seed=seed)
    optimized_pred = predict(model, x_test)
    future = predict(model, normalized[-window:][None, :, :])[0] * scales
    result = {
        'window': window, 'horizon': 1, 'feature_names': features,
        'actual_tail': (y_test[-1] * scales).tolist(),
        'predicted_tail': (optimized_pred[-1] * scales).tolist(),
        'future_prediction': future.tolist(),
        'baseline_mae': float(mae(y_test, baseline_pred)),
        'optimized_mae': float(mae(y_test, optimized_pred)),
        'optimized_rmse': float(np.sqrt(np.mean((y_test - optimized_pred) ** 2))),
        'prediction_trend': float(np.mean(future - values[-1])),
        'optimized_parameters': params, 'optimizer_validation_mae': float(val_mae),
        'optimizer_history': history, 'training_loss': baseline_loss,
    }
    _STATE['prediction'] = result
    return _jsonable(result)


def optimize(tasks: int = 50, vms: int = 12, seed: int = 42, population_size: int = 24, iterations: int = 20):
    rows = []
    for algorithm in ('ga', 'pso', 'psoga'):
        rows.append(run_algorithm(algorithm, num_tasks=tasks, num_vms=vms, population_size=population_size, iterations=iterations, seed=seed))
    comparison = []
    for row in rows:
        comparison.append({
            'algorithm': row['algorithm'], 'fitness': float(row['best_fitness']),
            'makespan': float(row['makespan']), 'runtime': float(row['running_time']),
            'migration_count': int(row['migration_count']), 'migration_time': float(row['migration_time']),
            'energy': float(row['energy_kwh']), 'sla_violations': 0,
        })
    winner = min(comparison, key=lambda x: x['fitness'])
    result = {'results': comparison, 'winner': winner, 'seed': seed, 'tasks': tasks, 'vms': vms}
    _STATE['comparison'] = result
    return _jsonable(result)


def decide(current_capacity: int = None, minimum: int = 1, maximum: int = 20, safe_utilization: float = 0.75, cooldown_seconds: int = 300, dry_run: bool = True):
    if current_capacity is None:
        from app.services.autoscaler import autoscaler
        current_capacity = autoscaler.get_status()['active']
        
    analysis = _STATE.get('analysis') or {}
    prediction = _STATE.get('prediction') or {}
    demand = float(analysis.get('estimated_future_demand', 0.0))
    if prediction.get('future_prediction'):
        demand = max(demand, float(np.mean(prediction['future_prediction'][:3])))
    engine = ResourceDecisionEngine(minimum, maximum, safe_utilization, cooldown_seconds)
    decision = engine.decide(current_capacity, demand, dry_run)
    result = {'current_capacity': decision.current_capacity, 'predicted_demand': demand,
              'recommended_capacity': decision.recommended_capacity, 'scaling_action': decision.action,
              'reason': decision.reason, 'minimum_capacity': minimum, 'maximum_capacity': maximum,
              'cooldown_seconds': cooldown_seconds, 'dry_run': dry_run, 'timestamp': time.time()}
    _STATE['decision'] = result
    return _jsonable(result)


def full_pipeline(source='E-commerce', path=None, data=None, tasks=50, vms=12, seed=42, dry_run=True):
    ingestion = ingest(source=source, path=path, data=data, seed=seed)
    
    # 1. Analyze and Predict workload
    try:
        prediction = _prediction(_STATE['df'], seed=seed)
    except ValueError:
        prediction = {}
        
    # 2. Make scaling decision based on current capacity and predicted demand
    decision = decide(dry_run=dry_run)
    
    # 3. Apply Resource Action (Update State) using Autoscaler
    from app.services.autoscaler import autoscaler
    target_vms = decision['recommended_capacity']
    scale_event = autoscaler.evaluate(target_vms, reason=decision['reason'])
    
    # Update current_capacity based on the active VMs from autoscaler
    _STATE['current_capacity'] = autoscaler.get_status()['active']
    
    # 4. Make optimization workload-sensitive
    dynamic_tasks = max(10, int(ingestion['analysis'].get('average_request_rate', tasks)))
    
    # 5. Optimize placement using the newly allocated resource capacity
    comparison = optimize(tasks=dynamic_tasks, vms=target_vms, seed=seed)
    
    report = _jsonable({
        'workload': ingestion, 
        'prediction': prediction, 
        'decision': decision, 
        'optimization': comparison, 
        'mode': 'simulation' if dry_run else 'aws'
    })
    
    out = Path(settings.results_path) / 'automation'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'latest_report.json').write_text(json.dumps(report, indent=2))
    pd.DataFrame(comparison['results']).to_csv(out / 'latest_optimization.csv', index=False)
    return report


def state():
    return {k: _jsonable(v) for k, v in _STATE.items() if k != 'df'}
