from fastapi import APIRouter
from app.schemas.api import OptimizationRequest, ExperimentRequest, ExperimentResponse
from app.services.experiments import run_experiment

router = APIRouter(prefix='/api/optimization', tags=['optimization'])

def _run(algorithm, req):
    return run_experiment(ExperimentRequest(algorithm=algorithm, tasks=req.tasks, vms=req.vms, seed=req.seed, population_size=req.population_size, iterations=req.iterations))

@router.post('/ga', response_model=ExperimentResponse, summary='Run the Genetic Algorithm baseline')
def ga(req: OptimizationRequest): return _run('ga', req)

@router.post('/pso', response_model=ExperimentResponse, summary='Run the Particle Swarm Optimization baseline')
def pso(req: OptimizationRequest): return _run('pso', req)

@router.post('/psoga', response_model=ExperimentResponse, summary='Run the integrated hybrid PSO-GA optimizer')
def psoga(req: OptimizationRequest): return _run('psoga', req)
