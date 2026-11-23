
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SimulationRequest(BaseModel):
    seed: int = 42
    day_type: Literal["weekday", "weekend"] = "weekday"


class SimulationResponse(BaseModel):
    id: int
    world_id: int
    status: str
    random_seed: int | None
    results_json: dict
    started_at: datetime | None
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)
