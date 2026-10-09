from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.autoscaler import autoscaler, VM, ScalingEvent

router = APIRouter(prefix="/api/autoscaling", tags=["autoscaling"])

class EvaluateRequest(BaseModel):
    target_capacity: int
    reason: str = "Manual scaling evaluation"

@router.get("/status")
def get_autoscaling_status() -> Dict[str, Any]:
    return autoscaler.get_status()

@router.get("/vms")
def get_vms() -> List[VM]:
    return autoscaler.provider.get_vms()

@router.get("/history")
def get_scaling_history() -> List[ScalingEvent]:
    return autoscaler.history

@router.post("/evaluate")
def evaluate_scaling(req: EvaluateRequest) -> ScalingEvent:
    event = autoscaler.evaluate(req.target_capacity, reason=req.reason)
    return event

@router.post("/scale")
def scale_manually(req: EvaluateRequest) -> ScalingEvent:
    event = autoscaler.evaluate(req.target_capacity, reason=req.reason)
    return event

