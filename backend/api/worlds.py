
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from models.dataset_db import DatasetDB
from models.project_db import ProjectDB
from models.world_db import WorldDB
from schemas.world_response import WorldGenerateRequest, WorldResponse
from ai.extractor import generate_world_config

router = APIRouter(tags=["Worlds"])


@router.post(
    "/api/projects/{project_id}/worlds/generate",
    response_model=WorldResponse,
)
def generate_world(
    project_id: int,
    request: WorldGenerateRequest,
    db: Session = Depends(get_db),
):
    project = db.get(ProjectDB, project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    statement = select(DatasetDB).where(
        DatasetDB.project_id == project_id,
        DatasetDB.status == "processed",
        DatasetDB.parsed_data.is_not(None),
    )

    if request.dataset_ids is not None:
        if not request.dataset_ids:
            raise HTTPException(
                status_code=400,
                detail="Select at least one dataset.",
            )

        statement = statement.where(
            DatasetDB.id.in_(request.dataset_ids)
        )

    datasets = db.scalars(statement.order_by(DatasetDB.id)).all()

    if not datasets:
        raise HTTPException(
            status_code=400,
            detail="No processed datasets found for this project.",
        )

    try:
        config = generate_world_config(datasets)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="World generation failed. Check backend logs for details.",
        ) from exc

    world = WorldDB(
        project_id=project_id,
        name=config.cafe_name,
        config_json=config.model_dump(mode="json"),
        is_baseline=True,
    )

    try:
        db.add(world)
        db.commit()
        db.refresh(world)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save the generated world.",
        ) from exc

    return world
