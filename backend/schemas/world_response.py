
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.world import WorldConfig


class WorldGenerateRequest(BaseModel):
    dataset_ids: list[int] | None = None


class WorldResponse(BaseModel):
    id: int
    project_id: int
    name: str
    parent_world_id: int | None
    change_summary: str | None
    config_json: WorldConfig
    is_baseline: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
