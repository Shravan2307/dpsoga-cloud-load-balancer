import asyncio
import time
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime
from src.workload.trace_adapter import GoogleClusterTraceAdapter
from app.services.automation import _STATE, _prediction, decide
from app.services.autoscaler import autoscaler

class TraceReplayService:
    def __init__(self):
        self.trace_df: Optional[pd.DataFrame] = None
        self.is_replaying = False
        self.current_index = 0
        self.dataset_info = {}
        self.window_seconds = 60
        self.replay_task = None
        self.replay_speed = 10 # 1 real second = 10 trace seconds

    def load_trace(self, file_path: str, window_seconds: int = 60) -> Dict[str, Any]:
        adapter = GoogleClusterTraceAdapter(file_path, window_seconds)
        self.trace_df = adapter.load_and_normalize()
        self.window_seconds = window_seconds
        self.current_index = 0
        self.is_replaying = False
        
        self.dataset_info = {
            'loaded': True,
            'dataset': 'Google Cluster Trace 2011 (v2) - task_usage',
            'records': len(self.trace_df),
            'window_seconds': window_seconds,
            'time_range': f"{self.trace_df['timestamp'].min()} to {self.trace_df['timestamp'].max()}"
        }
        return self.dataset_info

    def get_status(self) -> Dict[str, Any]:
        if self.trace_df is None:
            return {'loaded': False}
        
        current_workload = None
        if self.current_index > 0 and self.current_index <= len(self.trace_df):
            current_workload = self.trace_df.iloc[self.current_index - 1].to_dict()
            if isinstance(current_workload.get('timestamp'), pd.Timestamp):
                current_workload['timestamp'] = current_workload['timestamp'].isoformat()
                
        return {
            **self.dataset_info,
            'is_replaying': self.is_replaying,
            'current_position': self.current_index,
            'current_workload': current_workload
        }

    async def _replay_loop(self):
        while self.is_replaying and self.current_index < len(self.trace_df):
            # 1. Update the active workload window
            window_data = self.trace_df.iloc[:self.current_index + 1].copy()
            
            # Feed into existing pipeline state
            from src.workload.analyzer import analyze_workload
            _STATE['df'] = window_data
            _STATE['analysis'] = analyze_workload(window_data)
            
            # 2. CNN-LSTM prediction
            try:
                # Need at least 13 rows for CNN-LSTM
                if len(window_data) >= 13:
                    _prediction(window_data, seed=42)
            except Exception as e:
                pass
                
            # 3. Decision Engine
            try:
                dec = decide(dry_run=True)
                # 4. Autoscaler
                autoscaler.evaluate(dec['recommended_capacity'], reason="Google Trace Replay")
            except Exception as e:
                pass

            self.current_index += 1
            
            # Sleep according to replay speed
            await asyncio.sleep(self.window_seconds / self.replay_speed)
            
        self.is_replaying = False

    def start_replay(self, speed: int = 10):
        if self.trace_df is None:
            raise ValueError("No trace loaded")
        self.replay_speed = speed
        self.is_replaying = True
        
        try:
            loop = asyncio.get_running_loop()
            self.replay_task = loop.create_task(self._replay_loop())
        except RuntimeError:
            pass # No loop running

    def stop_replay(self):
        self.is_replaying = False
        if self.replay_task:
            self.replay_task.cancel()
            
    def step_replay(self):
        if self.trace_df is None:
            raise ValueError("No trace loaded")
        
        if self.current_index < len(self.trace_df):
            window_data = self.trace_df.iloc[:self.current_index + 1].copy()
            from src.workload.analyzer import analyze_workload
            _STATE['df'] = window_data
            _STATE['analysis'] = analyze_workload(window_data)
            
            try:
                if len(window_data) >= 13:
                    _prediction(window_data, seed=42)
            except Exception: pass
                
            try:
                dec = decide(dry_run=True)
                autoscaler.evaluate(dec['recommended_capacity'], reason="Google Trace Replay (Step)")
            except Exception: pass

            self.current_index += 1

trace_replay_service = TraceReplayService()

