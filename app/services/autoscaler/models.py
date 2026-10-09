from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid

class VMState(str, Enum):
    PROVISIONING = "PROVISIONING"
    RUNNING = "RUNNING"
    DRAINING = "DRAINING"
    TERMINATED = "TERMINATED"

class VM(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: VMState = VMState.PROVISIONING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    launched_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None
    metrics: Dict[str, float] = Field(default_factory=lambda: {"cpu": 0.0, "ram": 0.0})

class ScalingAction(str, Enum):
    SCALE_OUT = "SCALE OUT"
    SCALE_IN = "SCALE IN"
    MAINTAIN = "MAINTAIN"

class ScalingEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: ScalingAction
    reason: str
    vms_before: int
    vms_after: int
    target_vms: int

