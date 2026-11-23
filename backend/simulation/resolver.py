"""Turns a WorldConfig (which may have unknowns) into SimParams (complete),
recording every default it had to apply in `notes`."""
from dataclasses import dataclass, field
from schemas.world import WorldConfig

DEFAULT_ORDER_SECONDS = 45
DEFAULT_PREP_SECONDS = 120
DEFAULT_PATIENCE_MIN = 8.0
DEFAULT_ITEMS_PER_ORDER = 1.5
DEFAULT_ARRIVALS_PER_HOUR = 12.0


@dataclass
class SimMenuItem:
    name: str
    price: float
    unit_cost: float
    prep_seconds: float
    share: float
    ingredients: dict


@dataclass
class SimParams:
    day_type: str
    open_hour: float
    close_hour: float
    arrivals_per_hour: dict
    menu: list
    order_staff: int
    prep_staff: int
    shared_staff: int
    wage_per_hour_total: float
    inventory: dict          # only ingredients with a known starting quantity
    patience_min: float
    items_per_order: float
    order_seconds: float
    notes: list = field(default_factory=list)


def resolve(config: WorldConfig, day_type: str = "weekday") -> SimParams:
    notes = []

    # --- hours
    hrs = [h for h in config.operating_hours if h.day_type == day_type]
    if not hrs:
        hrs = config.operating_hours
        if hrs:
            notes.append(f"No {day_type} hours given; used the {hrs[0].day_type} hours.")
    if hrs:
        open_h, close_h = hrs[0].open_hour, hrs[0].close_hour
    else:
        open_h, close_h = 8.0, 22.0
        notes.append("DEFAULT operating hours 08:00-22:00 (none in data).")

    # --- demand
    rows = {d.hour: d.avg_arrivals for d in config.demand if d.day_type == day_type}
    arrivals = {h: 0.0 for h in range(24)}
    in_window = [h for h in range(int(open_h), int(-(-close_h // 1)))]
    if rows:
        mean_known = sum(rows.values()) / len(rows)
        for h in in_window:
            if h in rows:
                arrivals[h] = rows[h]
            else:
                arrivals[h] = mean_known
        if any(h not in rows for h in in_window):
            notes.append("Hours with no demand data were filled with the average of known hours.")
    else:
        for h in in_window:
            arrivals[h] = DEFAULT_ARRIVALS_PER_HOUR
        notes.append(f"DEFAULT demand: flat {DEFAULT_ARRIVALS_PER_HOUR:.0f} customers/hour "
                     "(no hourly demand in data). Results are illustrative only.")
    for m in config.demand_modifiers:
        if m.day_type == day_type:
            for h in range(24):
                if m.start_hour <= h < m.end_hour:
                    arrivals[h] *= m.multiplier

    # --- menu
    shares = [m.popularity_share for m in config.menu]
    if any(s is None for s in shares) or sum(s for s in shares if s) == 0:
        shares = [1 / len(config.menu)] * len(config.menu)
        notes.append("Menu popularity unknown; assumed all items equally popular.")
    else:
        total = sum(shares)
        shares = [s / total for s in shares]
    menu = []
    for m, s in zip(config.menu, shares):
        if m.prep_time_seconds is None:
            notes.append(f"DEFAULT prep time {DEFAULT_PREP_SECONDS}s for '{m.name}'.")
        menu.append(SimMenuItem(
            name=m.name, price=m.price, unit_cost=m.unit_cost or 0.0,
            prep_seconds=m.prep_time_seconds or DEFAULT_PREP_SECONDS, share=s,
            ingredients={i.ingredient: i.quantity for i in m.ingredients}))
    if any(m.unit_cost is None for m in config.menu):
        notes.append("Some item costs unknown (treated as 0); profit is overstated.")

    # --- staff
    order = sum(s.count for s in config.staff if s.duties == "order_taking")
    prep = sum(s.count for s in config.staff if s.duties == "preparation")
    both = sum(s.count for s in config.staff if s.duties == "both")
    if order + prep + both == 0:
        both = 1
        notes.append("DEFAULT 1 staff member (none in data).")
    if any(s.hourly_wage is None for s in config.staff):
        notes.append("Some wages unknown (treated as 0); staff cost is understated.")
    wages = sum(s.count * (s.hourly_wage or 0) for s in config.staff)

    # --- inventory
    inv = {i.ingredient: i.starting_quantity for i in config.inventory
           if i.starting_quantity is not None}
    if not inv:
        notes.append("Inventory not modeled (no stock levels in data); stock never runs out.")

    cb = config.customer_behavior
    if cb.avg_patience_minutes is None:
        notes.append(f"DEFAULT customer patience {DEFAULT_PATIENCE_MIN:.0f} min.")
    if cb.avg_items_per_order is None:
        notes.append(f"DEFAULT {DEFAULT_ITEMS_PER_ORDER} items per order.")

    return SimParams(
        day_type=day_type, open_hour=open_h, close_hour=close_h,
        arrivals_per_hour=arrivals, menu=menu, order_staff=order, prep_staff=prep,
        shared_staff=both, wage_per_hour_total=wages, inventory=inv,
        patience_min=cb.avg_patience_minutes or DEFAULT_PATIENCE_MIN,
        items_per_order=cb.avg_items_per_order or DEFAULT_ITEMS_PER_ORDER,
        order_seconds=DEFAULT_ORDER_SECONDS, notes=notes)