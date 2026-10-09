from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_THRESHOLDS = {
    'low_intensity': 0.35,
    'moderate_intensity': 0.60,
    'high_intensity': 0.80,
    'bursty_volatility': 0.12,
    'overload_probability': 0.65,
}


def _safe_mean(df, column):
    return float(df[column].mean()) if column in df and len(df) else 0.0


def _safe_peak(df, column):
    return float(df[column].max()) if column in df and len(df) else 0.0


def analyze_workload(df: pd.DataFrame, thresholds: dict | None = None) -> dict:
    if df is None or df.empty:
        raise ValueError('Cannot analyze an empty workload.')
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    numeric = df.select_dtypes(include=[np.number]).copy()
    if numeric.empty:
        raise ValueError('Workload has no numeric columns after preprocessing.')
    for c in ['cpu', 'memory', 'network']:
        if c not in numeric:
            numeric[c] = 0.0
    intensity_series = numeric[['cpu', 'memory', 'network']].mean(axis=1).clip(0, 1)
    intensity = float(intensity_series.mean())
    volatility = float(intensity_series.diff().abs().mean() or 0.0)
    x = np.arange(len(intensity_series), dtype=float)
    trend = float(np.polyfit(x, intensity_series.to_numpy(), 1)[0]) if len(x) > 1 else 0.0
    estimated_future = float(np.clip(intensity_series.iloc[-1] + trend * min(10, len(df) / 4), 0, 1))
    overload_probability = float(np.clip(0.55 * estimated_future + 0.45 * intensity, 0, 1))
    underutilization_probability = float(np.clip(1 - intensity, 0, 1))
    if overload_probability >= t['overload_probability'] or intensity >= t['high_intensity']:
        classification = 'OVERLOADED'
    elif volatility >= t['bursty_volatility']:
        classification = 'BURSTY'
    elif intensity >= t['high_intensity']:
        classification = 'HIGH'
    elif intensity >= t['moderate_intensity']:
        classification = 'MODERATE'
    else:
        classification = 'LOW'
    return {
        'rows': int(len(df)),
        'columns': list(df.columns),
        'average_cpu': _safe_mean(df, 'cpu'), 'peak_cpu': _safe_peak(df, 'cpu'),
        'average_memory': _safe_mean(df, 'memory'), 'peak_memory': _safe_peak(df, 'memory'),
        'average_network': _safe_mean(df, 'network'), 'peak_network': _safe_peak(df, 'network'),
        'average_request_rate': _safe_mean(df, 'requests'), 'peak_request_rate': _safe_peak(df, 'requests'),
        'average_latency': _safe_mean(df, 'latency'), 'peak_latency': _safe_peak(df, 'latency'),
        'workload_intensity': intensity, 'workload_volatility': volatility, 'trend': trend,
        'estimated_future_demand': estimated_future,
        'overload_probability': overload_probability,
        'underutilization_probability': underutilization_probability,
        'classification': classification,
        'thresholds': t,
    }
