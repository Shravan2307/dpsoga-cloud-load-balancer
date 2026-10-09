from __future__ import annotations

import math
from dataclasses import dataclass

@dataclass
class ResourceDecision:
    current_capacity: int
    predicted_demand: float
    recommended_capacity: int
    action: str
    reason: str
    dry_run: bool

class ResourceDecisionEngine:
    def __init__(self, minimum_capacity=1, maximum_capacity=20, safe_utilization=0.75, cooldown_seconds=300):
        if minimum_capacity < 1 or maximum_capacity < minimum_capacity:
            raise ValueError('Capacity limits are invalid.')
        self.minimum_capacity = minimum_capacity
        self.maximum_capacity = maximum_capacity
        self.safe_utilization = safe_utilization
        self.cooldown_seconds = cooldown_seconds
    def decide(self, current_capacity: int, predicted_demand: float, dry_run: bool = True) -> ResourceDecision:
        target = math.ceil(max(1.0, predicted_demand / max(self.safe_utilization, 0.01) * current_capacity))
        recommended = min(max(target, self.minimum_capacity), self.maximum_capacity)
        action = 'SCALE OUT' if recommended > current_capacity else 'SCALE IN' if recommended < current_capacity else 'MAINTAIN'
        return ResourceDecision(current_capacity, predicted_demand, recommended, action,
            f'Predicted demand is {predicted_demand:.3f}; safe utilization is {self.safe_utilization:.3f}.', dry_run)
