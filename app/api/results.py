from fastapi import APIRouter
from app.services.experiments import read_result

router = APIRouter(prefix='/api/results', tags=['results'])

@router.get('/phase1', summary='Read the generated Phase 1 results')
def phase1(): return read_result('phase1_results.csv')

@router.get('/phase2', summary='Read the generated Phase 2 results')
def phase2(): return read_result('phase2_results.json')
