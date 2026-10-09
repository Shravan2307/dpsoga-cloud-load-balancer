import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import math

class GoogleClusterTraceAdapter:
    """
    Adapter for Google Cluster Trace (2011/v2).
    Reads the `task_usage` table and normalizes it into the project's standard workload format.
    
    Dataset: Google Cluster Trace 2011 (v2)
    Source: https://github.com/google/cluster-data
    Table: task_usage (20 columns)
    """
    def __init__(self, file_path: str, window_seconds: int = 60):
        self.file_path = file_path
        self.window_seconds = window_seconds
        
        self.columns = [
            'start_time', 'end_time', 'job_id', 'task_index', 'machine_id',
            'cpu_rate', 'canonical_memory_usage', 'assigned_memory_usage',
            'unmapped_page_cache', 'total_page_cache', 'maximum_memory_usage',
            'disk_io_time', 'local_disk_space_usage', 'maximum_cpu_rate',
            'maximum_disk_io_time', 'cycles_per_instruction',
            'memory_accesses_per_instruction', 'sample_portion',
            'unmapped_page_cache_memory_usage', 'page_cache_memory_usage'
        ]

    def load_and_normalize(self) -> pd.DataFrame:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Google Cluster Trace file not found at {self.file_path}")
            
        # Read the raw trace (chunking can be used for huge files, reading whole for sample)
        df = pd.read_csv(self.file_path, names=self.columns, usecols=['start_time', 'end_time', 'cpu_rate', 'canonical_memory_usage'])
        
        # Google timestamps are in microseconds
        df['start_sec'] = df['start_time'] / 1e6
        df = df[df['start_sec'] >= 0].copy()
        
        if df.empty:
            raise ValueError("Parsed trace file is empty or contains no valid timestamps.")
            
        max_time = int(math.ceil(df['start_sec'].max()))
        if max_time == 0: max_time = self.window_seconds
        
        bins = range(0, max_time + self.window_seconds * 2, self.window_seconds)
        df['window'] = pd.cut(df['start_sec'], bins=bins, labels=bins[:-1], right=False)
        
        agg_df = df.groupby('window', observed=False).agg(
            cpu_rate=('cpu_rate', 'mean'),
            memory_usage=('canonical_memory_usage', 'mean'),
            task_count=('start_sec', 'count')
        ).reset_index()
        
        # Forward fill empty windows
        agg_df = agg_df.ffill().fillna(0)
        
        normalized = pd.DataFrame()
        base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        normalized['timestamp'] = [base_time + timedelta(seconds=int(w)) for w in agg_df['window']]
        
        # Map raw trace metrics to Derived Workload Metrics
        # Raw cpu_rate is 0.0 to 1.0. Scale to 0-100 percentage.
        normalized['cpu'] = np.clip(agg_df['cpu_rate'] * 100 * 5, 0, 100) # Multiplier for visibility in demo
        normalized['memory'] = np.clip(agg_df['memory_usage'] * 100 * 5, 0, 100)
        
        # Workload intensity derived from active task events in the window
        normalized['requests'] = agg_df['task_count'] * 15 
        
        # Network and latency are unavailable in `task_usage`. Derived defensively.
        normalized['network'] = np.clip(agg_df['cpu_rate'] * 50 + 20, 0, 100)
        normalized['latency'] = np.clip(agg_df['task_count'] * 2 + 10, 0, 1000)
        
        return normalized

