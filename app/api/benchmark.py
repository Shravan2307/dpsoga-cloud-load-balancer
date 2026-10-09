from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.benchmark import run_benchmark

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

class BenchmarkRequest(BaseModel):
    dataset: str = "data/raw/google_cluster_trace/sample_task_usage.csv"
    window_seconds: int = 60
    algorithms: List[str] = ["ga", "pso", "psoga"]
    max_records: int = 100
    seed: int = 42

@router.post("/google-trace/run")
def run_google_trace_benchmark(req: BenchmarkRequest) -> Dict[str, Any]:
    try:
        result = run_benchmark(
            dataset_path=req.dataset,
            window_seconds=req.window_seconds,
            algorithms=req.algorithms,
            seed=req.seed,
            max_records=req.max_records
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

