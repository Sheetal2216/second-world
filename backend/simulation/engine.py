import math
import numpy as np
import simpy
from simulation.resolver import SimParams


def run_simulation(p: SimParams, seed: int = 0, snapshot_every_min: float = 5.0) -> dict:
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    duration = (p.close_hour - p.open_hour) * 60            # minutes since opening

    two_stage = p.order_staff > 0 and (p.prep_staff + p.shared_staff) > 0
    if two_stage:
        order_res = simpy.Resource(env, capacity=p.order_staff)
        prep_res = simpy.Resource(env, capacity=p.prep_staff + p.shared_staff)
        total_capacity = p.order_staff + p.prep_staff + p.shared_staff
    else:
        total_capacity = max(1, p.order_staff + p.prep_staff + p.shared_staff)
        order_res = prep_res = simpy.Resource(env, capacity=total_capacity)

    stock = dict(p.inventory)
    shares = np.array([m.share for m in p.menu])
    m = dict(arrived=0, served=0, abandoned=0, unfinished=0, stockouts=0, revenue=0.0,
             lost_revenue=0.0, ingredient_cost=0.0, busy=0.0, waits=[], consumed={})
    series = []

    def prepare(picks):
        total_prep, got_any = 0.0, False
        for idx in picks:
            item = p.menu[idx]
            if any(ing in stock and stock[ing] < q for ing, q in item.ingredients.items()):
                m["stockouts"] += 1
                m["lost_revenue"] += item.price
                continue
            for ing, q in item.ingredients.items():
                if ing in stock:
                    stock[ing] -= q
                m["consumed"][ing] = m["consumed"].get(ing, 0) + q
            m["revenue"] += item.price
            m["ingredient_cost"] += item.unit_cost
            total_prep += item.prep_seconds / 60
            got_any = True
        if total_prep:
            yield env.timeout(total_prep)
            m["busy"] += total_prep
        if got_any:
            m["served"] += 1

    def customer(arrival_delay):
        yield env.timeout(arrival_delay)
        m["arrived"] += 1
        arrival = env.now
        n_items = 1 + int(rng.poisson(max(p.items_per_order - 1, 0)))
        picks = rng.choice(len(p.menu), size=n_items, p=shares)
        potential = sum(p.menu[i].price for i in picks)
        patience = rng.exponential(p.patience_min)
        with order_res.request() as req:
            got = yield req | env.timeout(patience)
            if req not in got:
                m["abandoned"] += 1
                m["lost_revenue"] += potential
                return
            m["waits"].append(env.now - arrival)
            yield env.timeout(p.order_seconds / 60)
            m["busy"] += p.order_seconds / 60
            if not two_stage:
                yield from prepare(picks)
        if two_stage:
            with prep_res.request() as req2:
                yield req2
                yield from prepare(picks)

    # schedule arrivals (non-homogeneous Poisson: per-hour counts, uniform within the hour)
    for h in range(int(p.open_hour), math.ceil(p.close_hour)):
        lo, hi = max(h, p.open_hour), min(h + 1, p.close_hour)
        n = int(rng.poisson(p.arrivals_per_hour.get(h, 0) * (hi - lo)))
        for t in rng.uniform(lo, hi, size=n):
            env.process(customer((t - p.open_hour) * 60))

    def monitor():
        while True:
            q = len(order_res.queue) + (len(prep_res.queue) if two_stage else 0)
            busy_now = order_res.count + (prep_res.count if two_stage else 0)
            series.append(dict(minute=round(env.now, 1),
                               clock_hour=round(p.open_hour + env.now / 60, 2),
                               queue_length=q, staff_busy=busy_now,
                               revenue=round(m["revenue"], 2), served=m["served"],
                               abandoned=m["abandoned"]))
            yield env.timeout(snapshot_every_min)
    env.process(monitor())
    env.run(until=duration)

    waits = np.array(m["waits"]) if m["waits"] else np.array([0.0])
    staff_cost = p.wage_per_hour_total * duration / 60
    arrived = m["arrived"]
    return dict(
        summary=dict(
            customers_arrived=arrived, orders_served=m["served"], abandoned=m["abandoned"],
            abandonment_rate=round(m["abandoned"] / arrived, 3) if arrived else 0.0,
            stockout_items=m["stockouts"], revenue=round(m["revenue"], 2),
            lost_revenue=round(m["lost_revenue"], 2),
            ingredient_cost=round(m["ingredient_cost"], 2), staff_cost=round(staff_cost, 2),
            profit=round(m["revenue"] - m["ingredient_cost"] - staff_cost, 2),
            avg_wait_min=round(float(waits.mean()), 2),
            p90_wait_min=round(float(np.percentile(waits, 90)), 2),
            max_wait_min=round(float(waits.max()), 2),
            staff_utilization=round(min(m["busy"] / (total_capacity * duration), 1.0), 3),
            ingredients_consumed={k: round(v, 1) for k, v in m["consumed"].items()}),
        timeseries=series, assumptions_used=p.notes, seed=seed)