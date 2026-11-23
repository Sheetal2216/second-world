
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class SimulationDB(Base):
    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    world_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="completed",
    )

    random_seed: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    results_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
