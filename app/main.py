from fastapi import FastAPI
from app.api.experiments import router as experiments_router
from app.api.optimization import router as optimization_router
from app.api.prediction import router as prediction_router
from app.api.results import router as results_router
from app.api.workload import router as workload_router
from app.api.automation import router as automation_router
from app.api.cloud import router as cloud_router

app = FastAPI(
    title='DPSO-GA Intelligent Cloud Resource Optimization and Auto-Scaling System Using CNN-LSTM',
    version='0.2.0',
    description='Local-first automation API around the existing DPSO-GA research implementation. AWS execution is optional and dry-run by default.',
)

@app.get('/health', tags=['system'], summary='Check backend health')
def health():
    return {'status': 'healthy'}

app.include_router(experiments_router)
app.include_router(optimization_router)
app.include_router(prediction_router)
app.include_router(results_router)
app.include_router(workload_router)
app.include_router(automation_router)
app.include_router(cloud_router)

from app.api.autoscaling import router as autoscaling_router
app.include_router(autoscaling_router)

from app.api.google_trace import router as google_trace_router
app.include_router(google_trace_router)

from app.api.benchmark import router as benchmark_router
app.include_router(benchmark_router)

import asyncio
from app.core.config import settings
from app.services.autoscaler import autoscaler

@app.on_event("startup")
async def startup_event():
    if settings.autoscaling_enabled:
        asyncio.create_task(autoscaler.background_loop(interval=settings.autoscaling_interval))
