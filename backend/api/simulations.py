
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models.world_db import WorldDB
from models.simulation_db import SimulationDB
from schemas.simulation import SimulationRequest, SimulationResponse
from schemas.world import WorldConfig
from simulation.engine import run_simulation
from simulation.resolver import resolve

router = APIRouter(prefix="/api", tags=["Simulations"])


@router.post(
    "/worlds/{world_id}/simulate",
    response_model=SimulationResponse,
)
def create_simulation(
    world_id: int,
    request: SimulationRequest,
    db: Session = Depends(get_db),
):
    world = db.query(WorldDB).filter(WorldDB.id == world_id).first()

    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    try:
        config = WorldConfig.model_validate(world.config_json)

        started_at = datetime.now(timezone.utc)

        params = resolve(config, day_type=request.day_type)

        results = run_simulation(
            params,
            seed=request.seed,
        )

        results["day_type"] = request.day_type

        completed_at = datetime.now(timezone.utc)

        simulation = SimulationDB(
            world_id=world_id,
            status="completed",
            random_seed=request.seed,
            results_json=results,
            started_at=started_at,
            completed_at=completed_at,
        )

        db.add(simulation)
        db.commit()
        db.refresh(simulation)

        return simulation

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {str(error)}",
        )


@router.get(
    "/simulations/{simulation_id}",
    response_model=SimulationResponse,
)
def get_simulation(
    simulation_id: int,
    db: Session = Depends(get_db),
):
    simulation = (
        db.query(SimulationDB)
        .filter(SimulationDB.id == simulation_id)
        .first()
    )

    if not simulation:
        raise HTTPException(
            status_code=404,
            detail="Simulation not found",
        )

    return simulation


@router.get(
    "/worlds/{world_id}/simulations",
    response_model=list[SimulationResponse],
)
def get_world_simulations(
    world_id: int,
    db: Session = Depends(get_db),
):
    world = db.query(WorldDB).filter(WorldDB.id == world_id).first()

    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    return (
        db.query(SimulationDB)
        .filter(SimulationDB.world_id == world_id)
        .order_by(SimulationDB.completed_at.desc())
        .all()
    )
