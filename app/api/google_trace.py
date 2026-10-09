from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.services.trace_replay import trace_replay_service
from app.core.config import settings

router = APIRouter(prefix="/api/workload/google-trace", tags=["workload", "google-trace"])

class LoadRequest(BaseModel):
    file_path: str = "data/raw/google_cluster_trace/sample_task_usage.csv"
    window_seconds: int = 60

class ReplayRequest(BaseModel):
    speed: int = 10

@router.post("/load")
def load_trace(req: LoadRequest) -> Dict[str, Any]:
    try:
        return trace_replay_service.load_trace(req.file_path, req.window_seconds)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
def get_status() -> Dict[str, Any]:
    return trace_replay_service.get_status()

@router.post("/run")
def run_trace(req: ReplayRequest):
    try:
        trace_replay_service.start_replay(req.speed)
        return {"status": "Replay started", "speed": req.speed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pause")
def pause_trace():
    trace_replay_service.stop_replay()
    return {"status": "Replay paused"}
    
@router.post("/step")
def step_trace():
    try:
        trace_replay_service.step_replay()
        return {"status": "Stepped successfully", "current_position": trace_replay_service.current_index}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

