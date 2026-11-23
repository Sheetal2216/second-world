
from typing import Literal
from pydantic import BaseModel, Field, model_validator

DayType = Literal["weekday", "weekend"]


class OperatingHours(BaseModel):
    day_type: DayType
    open_hour: float = Field(ge=0, lt=24)
    close_hour: float = Field(gt=0, le=24)

    @model_validator(mode="after")
    def close_after_open(self):
        if self.close_hour <= self.open_hour:
            raise ValueError("close_hour must be after open_hour")
        return self


class StaffRole(BaseModel):
    role: str
    count: int = Field(ge=0)
    hourly_wage: float | None = Field(default=None, ge=0)
    duties: Literal["order_taking", "preparation", "both"] = "both"


class IngredientUse(BaseModel):
    ingredient: str
    quantity: float = Field(gt=0)


class MenuItem(BaseModel):
    name: str
    category: str | None = None
    price: float = Field(gt=0)
    unit_cost: float | None = Field(default=None, ge=0)
    prep_time_seconds: float | None = Field(default=None, gt=0)
    popularity_share: float | None = Field(default=None, ge=0, le=1)
    ingredients: list[IngredientUse] = Field(default_factory=list)


class InventoryItem(BaseModel):
    ingredient: str
    unit: str
    starting_quantity: float | None = Field(default=None, ge=0)
    unit_cost: float | None = Field(default=None, ge=0)
    reorder_level: float | None = Field(default=None, ge=0)


class HourlyDemand(BaseModel):
    day_type: DayType
    hour: int = Field(ge=0, le=23)
    avg_arrivals: float = Field(ge=0)


class DemandModifier(BaseModel):
    description: str
    day_type: DayType
    start_hour: float = Field(ge=0, lt=24)
    end_hour: float = Field(gt=0, le=24)
    multiplier: float = Field(gt=0)


class CustomerBehavior(BaseModel):
    avg_patience_minutes: float | None = Field(default=None, gt=0)
    avg_items_per_order: float | None = Field(default=None, gt=0)


class Assumption(BaseModel):
    field_path: str
    assumed_value: str
    reason: str


class MissingInformation(BaseModel):
    field_path: str
    why_needed: str


class WorldConfig(BaseModel):
    schema_version: int = 1
    cafe_name: str
    currency: str = "INR"
    seating_capacity: int | None = Field(default=None, ge=0)

    operating_hours: list[OperatingHours]
    staff: list[StaffRole]
    menu: list[MenuItem] = Field(min_length=1)

    inventory: list[InventoryItem] = Field(default_factory=list)
    demand: list[HourlyDemand] = Field(default_factory=list)
    demand_modifiers: list[DemandModifier] = Field(default_factory=list)

    customer_behavior: CustomerBehavior = Field(
        default_factory=CustomerBehavior
    )
    assumptions: list[Assumption] = Field(default_factory=list)
    missing_information: list[MissingInformation] = Field(
        default_factory=list
    )
    source_dataset_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_menu(self):
        names = [item.name.strip().casefold() for item in self.menu]

        if any(not name for name in names):
            raise ValueError("Menu item names cannot be empty")

        if len(names) != len(set(names)):
            raise ValueError("Menu item names must be unique")

        shares = [item.popularity_share for item in self.menu]

        if all(share is not None for share in shares):
            total = sum(shares)
            if not 0.95 <= total <= 1.05:
                raise ValueError(
                    "popularity_share values should sum to about 1"
                )

        return self
