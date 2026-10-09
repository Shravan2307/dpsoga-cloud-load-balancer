from fastapi import APIRouter
from app.schemas.api import ExperimentRequest, ExperimentResponse
from app.services.experiments import run_experiment

router = APIRouter(prefix='/api/experiments', tags=['experiments'])

@router.post('/run', response_model=ExperimentResponse, summary='Run one configured cloud scheduling experiment')
def run(req: ExperimentRequest):
    return run_experiment(req)
