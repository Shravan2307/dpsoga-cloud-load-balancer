from fastapi import APIRouter, HTTPException
from app.schemas.api import GenericResult, ScaleRequest
from app.services.cloud import AWSCloudAdapter, CloudWatchMonitor, SimulationAdapter

router = APIRouter(prefix='/api/cloud', tags=['cloud'])

def _adapter(mode: str, dry_run: bool):
    if mode.lower() == 'aws':
        return AWSCloudAdapter(dry_run=dry_run)
    return SimulationAdapter()

@router.get('/status', response_model=GenericResult, summary='Read simulation or AWS execution status')
def status(mode: str = 'simulation', dry_run: bool = True):
    try: return {'status': 'available', 'result': _adapter(mode, dry_run).status()}
    except RuntimeError as exc: raise HTTPException(status_code=503, detail=str(exc)) from exc

@router.get('/metrics', response_model=GenericResult, summary='Read cloud metrics or dry-run metric status')
def metrics(mode: str = 'simulation', dry_run: bool = True):
    try: return {'status': 'available', 'result': _adapter(mode, dry_run).metrics()}
    except RuntimeError as exc: raise HTTPException(status_code=503, detail=str(exc)) from exc

@router.post('/scale', response_model=GenericResult, summary='Apply or dry-run a capacity scaling decision')
def scale(req: ScaleRequest, mode: str = 'simulation'):
    try: return {'status': 'submitted', 'result': _adapter(mode, req.dry_run).scale(req.desired_capacity, req.dry_run)}
    except RuntimeError as exc: raise HTTPException(status_code=503, detail=str(exc)) from exc

from app.services.cloud import S3Store

@router.get('/presigned_url', response_model=GenericResult, summary='Generate a presigned S3 URL for a specific file key')
def presigned_url(key: str, expiration: int = 3600):
    try:
        store = S3Store()
        url = store.generate_presigned_url(key, expiration=expiration)
        return {'status': 'generated', 'result': {'url': url, 'key': key, 'expiration': expiration}}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

