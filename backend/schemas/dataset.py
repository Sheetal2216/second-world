from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DatasetCreate(BaseModel):
    filename: str
    file_type: str
    storage_path: str
    status: str = "pending"
    parsed_data: dict[str, Any] | None = None


class DatasetResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    file_type: str
    storage_path: str
    status: str
    parsed_data: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)