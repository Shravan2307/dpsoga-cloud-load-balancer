from typing import Any, Literal
from pydantic import BaseModel, Field

Algorithm = Literal['ga', 'pso', 'psoga']

class ExperimentRequest(BaseModel):
    algorithm: Algorithm = 'psoga'
    tasks: int = Field(50, ge=1, le=100000)
    vms: int = Field(12, ge=1, le=10000)
    seed: int = 42
    datacenters: int = Field(3, ge=1)
    hosts_per_datacenter: int = Field(4, ge=1)
    population_size: int = Field(24, ge=2)
    iterations: int = Field(20, ge=1)

class ExperimentResponse(BaseModel):
    algorithm: str
    seed: int
    makespan: float
    fitness: float
    runtime: float
    waiting_time: float
    response_time: float
    migration_count: int
    migration_time: float
    energy: float
    cpu_utilization: float
    ram_utilization: float
    storage_utilization: float
    bandwidth_utilization: float

class OptimizationRequest(BaseModel):
    tasks: int = Field(50, ge=1, le=100000)
    vms: int = Field(12, ge=1, le=10000)
    seed: int = 42
    population_size: int = Field(24, ge=2)
    iterations: int = Field(20, ge=1)

class PredictionTrainRequest(BaseModel):
    dataset: Literal['synthetic', 'google'] = 'synthetic'
    google_path: str | None = None
    seed: int = 42
    window: int = Field(5, ge=2)
    epochs: int = Field(2, ge=1)
    optimizer_population: int = Field(4, ge=2)
    optimizer_iterations: int = Field(2, ge=1)

class PredictionRequest(BaseModel):
    values: list[list[float]] = Field(..., min_length=5)
    model_id: str = 'latest'

class PredictionResponse(BaseModel):
    model_id: str
    prediction: list[float]
    feature_count: int

class GenericResult(BaseModel):
    status: str
    result: dict[str, Any]

class WorkloadAnalyzeRequest(BaseModel):
    source: str = 'E-commerce'
    path: str | None = None
    seed: int = 42

class WorkloadPipelineRequest(BaseModel):
    source: str = 'E-commerce'
    path: str | None = None
    tasks: int = Field(50, ge=1, le=100000)
    vms: int = Field(12, ge=1, le=10000)
    seed: int = 42
    dry_run: bool = True

class OptimizeRequest(BaseModel):
    tasks: int = Field(50, ge=1, le=100000)
    vms: int = Field(12, ge=1, le=10000)
    seed: int = 42
    population_size: int = Field(24, ge=2)
    iterations: int = Field(20, ge=1)

class ScaleRequest(BaseModel):
    desired_capacity: int = Field(..., ge=1)
    dry_run: bool = True

class DecisionRequest(BaseModel):
    current_capacity: int = Field(3, ge=1)
    minimum_capacity: int = Field(1, ge=1)
    maximum_capacity: int = Field(20, ge=1)
    safe_utilization: float = Field(0.75, gt=0, le=1)
    cooldown_seconds: int = Field(300, ge=0)
    dry_run: bool = True
