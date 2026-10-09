from fastapi import APIRouter, HTTPException
from app.schemas.api import DecisionRequest, GenericResult, OptimizeRequest
from app.services.automation import decide, optimize, state

router = APIRouter(prefix='/api', tags=['automation'])

@router.post('/optimize', response_model=GenericResult, summary='Compare GA, PSO, and PSO-GA on one workload')
def compare(req: OptimizeRequest):
    try:
        return {'status': 'completed', 'result': optimize(req.tasks, req.vms, req.seed, req.population_size, req.iterations)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post('/optimize/run', response_model=GenericResult, summary='Alias for optimization comparison')
def compare_alias(req: OptimizeRequest):
    return compare(req)

@router.get('/optimization/results', response_model=GenericResult, summary='Read the latest optimizer comparison')
def latest_optimization():
    return {'status': 'available', 'result': state().get('comparison') or {}}

@router.post('/decisions', response_model=GenericResult, summary='Generate a capacity decision from latest analysis/prediction')
def decision(req: DecisionRequest):
    try:
        return {'status': 'completed', 'result': decide(req.current_capacity, req.minimum_capacity, req.maximum_capacity, req.safe_utilization, req.cooldown_seconds, req.dry_run)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get('/decisions', response_model=GenericResult, summary='Read the latest resource decision')
def latest_decision():
    return {'status': 'available', 'result': state().get('decision') or {}}
