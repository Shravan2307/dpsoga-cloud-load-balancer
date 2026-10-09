from fastapi import APIRouter, File, HTTPException, UploadFile
from app.schemas.api import GenericResult, OptimizeRequest, WorkloadAnalyzeRequest, WorkloadPipelineRequest
from app.services.automation import ingest, optimize, full_pipeline, state, latest_dataframe, _prediction

router = APIRouter(prefix='/api/workload', tags=['workload'])

from app.services.automation import _jsonable, latest_dataframe, _prediction

@router.post('/upload', response_model=GenericResult, summary='Upload and validate a workload CSV')
async def upload(file: UploadFile = File(...), seed: int = 42):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail='Only CSV workload files are supported.')
    try:
        data = await file.read()
        if not data:
            raise ValueError('Uploaded CSV file is empty.')
        
        ingest_res = ingest(data=data, seed=seed)
        df = latest_dataframe()
        rows = len(df)
        
        result_payload = {
            'filename': file.filename,
            'row_count': rows,
            'detected_columns': list(df.columns),
            'workload_analysis': ingest_res['analysis'],
            'analysis': ingest_res['analysis'],
            'preview': ingest_res['preview']
        }
        
        if rows >= 13:
            try:
                result_payload['prediction'] = _prediction(df, seed=seed)
            except Exception as e:
                result_payload['prediction_error'] = str(e)
        else:
            result_payload['prediction_error'] = 'Insufficient rows for CNN-LSTM prediction (need at least 13).'
            
        return {'status': 'uploaded', 'result': _jsonable(result_payload)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post('/analyze', response_model=GenericResult, summary='Analyze a predefined or local workload')
def analyze(req: WorkloadAnalyzeRequest):
    try:
        return {'status': 'analyzed', 'result': ingest(source=req.source, path=req.path, seed=req.seed)}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post('/predict', response_model=GenericResult, summary='Run automatic workload prediction after ingestion')
def predict(req: WorkloadAnalyzeRequest):
    try:
        ingest(source=req.source, path=req.path, seed=req.seed)
        return {'status': 'predicted', 'result': _prediction(latest_dataframe(), req.seed)}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post('/pipeline', response_model=GenericResult, summary='Run analysis, prediction, comparison, and resource decision automatically')
def pipeline(req: WorkloadPipelineRequest):
    try:
        return {'status': 'completed', 'result': full_pipeline(source=req.source, path=req.path, tasks=req.tasks, vms=req.vms, seed=req.seed, dry_run=req.dry_run)}
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get('/state', response_model=GenericResult, summary='Read the latest automation state')
def latest_state():
    return {'status': 'available', 'result': state()}
