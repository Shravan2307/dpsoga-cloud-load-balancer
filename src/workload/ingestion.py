from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd

PROFILE_NAMES = ['E-commerce', 'Banking', 'Streaming', 'Education', 'Healthcare', 'SaaS', 'Custom']
ALIASES = {
    'timestamp': ['timestamp', 'time', 'datetime', 'date'],
    'cpu': ['cpu', 'cpu_utilization', 'cpu_usage', 'processor', 'processing'],
    'memory': ['memory', 'ram', 'ram_utilization', 'mem'],
    'network': ['network', 'bandwidth', 'network_utilization', 'bw'],
    'requests': ['requests', 'request_rate', 'request_count', 'throughput', 'traffic'],
    'latency': ['latency', 'response_time', 'response_latency', 'delay'],
}


def _canonical_columns(columns):
    normalized = {str(c).strip().lower().replace(' ', '_'): c for c in columns}
    rename = {}
    for canonical, candidates in ALIASES.items():
        for candidate in candidates:
            if candidate in normalized:
                rename[normalized[candidate]] = canonical
                break
    return rename


def _profile(name: str, n: int = 240, seed: int = 42) -> pd.DataFrame:
    if name == 'Custom':
        raise ValueError('Custom workload requires a CSV dataset.')
    rng = np.random.default_rng(seed)
    t = np.arange(max(n, 20), dtype=float)
    base = {
        'E-commerce': (0.62, 0.24, 1.25), 'Banking': (0.48, 0.08, 0.85),
        'Streaming': (0.70, 0.14, 1.10), 'Education': (0.38, 0.18, 0.60),
        'Healthcare': (0.52, 0.10, 0.75), 'SaaS': (0.56, 0.22, 0.95),
    }[name]
    level, volatility, request_scale = base
    burst = ((t % 48) > 36) * volatility * 0.8
    cpu = level + 0.10 * np.sin(t / 11) + burst + rng.normal(0, volatility * 0.12, len(t))
    memory = level * 0.78 + 0.06 * np.sin(t / 17) + rng.normal(0, 0.025, len(t))
    network = level * 0.65 + 0.12 * np.sin(t / 8) + rng.normal(0, 0.035, len(t))
    requests = request_scale * (100 + 25 * np.sin(t / 13) + burst * 100) + rng.normal(0, 4, len(t))
    latency = 80 + 45 * np.maximum(cpu - 0.65, 0) + rng.normal(0, 3, len(t))
    return pd.DataFrame({'timestamp': pd.date_range('2024-01-01', periods=len(t), freq='min'),
                         'cpu': np.clip(cpu, 0, 1), 'memory': np.clip(memory, 0, 1),
                         'network': np.clip(network, 0, 1), 'requests': np.clip(requests, 0, None),
                         'latency': np.clip(latency, 0, None)})


def load_workload(source: str = 'E-commerce', path: str | None = None,
                  data: bytes | BinaryIO | None = None, n: int = 240, seed: int = 42) -> pd.DataFrame:
    if data is not None:
        raw = BytesIO(data) if isinstance(data, bytes) else data
        try:
            df = pd.read_csv(raw)
        except pd.errors.EmptyDataError:
            raise ValueError('Workload dataset is empty.')
        except Exception as e:
            raise ValueError(f'Invalid CSV: {e}')
    elif path:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f'Workload CSV does not exist: {path}')
        df = pd.read_csv(file_path)
    else:
        return _profile(source, n=n, seed=seed)

    if df.empty:
        raise ValueError('Workload dataset is empty.')
    
    df = df.rename(columns=_canonical_columns(df.columns))
    
    required_cols = ['timestamp', 'cpu', 'memory', 'network', 'requests', 'latency']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
        
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    if df['timestamp'].isna().all():
        raise ValueError("Timestamp column contains no valid datetimes.")
        
    df = df.sort_values('timestamp', na_position='last')
    
    numeric = ['cpu', 'memory', 'network', 'requests', 'latency']
    for column in numeric:
        # Convert to numeric, coercing errors to NaN
        df[column] = pd.to_numeric(df[column], errors='coerce')
        if df[column].isna().any():
            raise ValueError(f"Column '{column}' contains invalid numeric values or missing data.")
            
    # Clip normalized values
    for column in ['cpu', 'memory', 'network']:
        if df[column].max() > 1.5:
            df[column] = df[column] / 100.0
        df[column] = df[column].clip(0, 1)
        
    return df.reset_index(drop=True)
