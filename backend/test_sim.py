import copy, json
from schemas.world import WorldConfig
from simulation.resolver import resolve
from simulation.engine import run_simulation

example = {
    "cafe_name": "Brew & Bites", "seating_capacity": 24,
    "operating_hours": [{"day_type": "weekday", "open_hour": 8, "close_hour": 22},
                        {"day_type": "weekend", "open_hour": 9, "close_hour": 23}],
    "staff": [{"role": "barista", "count": 2, "hourly_wage": 120, "duties": "preparation"},
              {"role": "cashier", "count": 1, "hourly_wage": 100, "duties": "order_taking"}],
    "menu": [
        {"name": "Cappuccino", "price": 160, "unit_cost": 45, "prep_time_seconds": 150, "popularity_share": 0.5,
         "ingredients": [{"ingredient": "milk", "quantity": 150}, {"ingredient": "coffee beans", "quantity": 18}]},
        {"name": "Veg Sandwich", "price": 140, "unit_cost": 50, "prep_time_seconds": 240, "popularity_share": 0.5,
         "ingredients": [{"ingredient": "bread", "quantity": 2}]}],
    "inventory": [{"ingredient": "milk", "unit": "ml", "starting_quantity": 20000},
                  {"ingredient": "coffee beans", "unit": "g", "starting_quantity": 3000},
                  {"ingredient": "bread", "unit": "pcs", "starting_quantity": 60}],
    "demand": [{"day_type": "weekday", "hour": h, "avg_arrivals": a}
               for h, a in [(8, 10), (9, 18), (12, 25), (18, 30), (20, 22)]],
    "customer_behavior": {"avg_patience_minutes": None},
}
base = WorldConfig.model_validate(example)
s = run_simulation(resolve(base), seed=1)
print("BASELINE", json.dumps(s["summary"], indent=1))
print("NOTES", s["assumptions_used"])

# Scenario: +1 barista
sc = copy.deepcopy(example); sc["staff"][0]["count"] = 3
s2 = run_simulation(resolve(WorldConfig.model_validate(sc)), seed=1)
for k in ["orders_served","abandoned","revenue","avg_wait_min","staff_utilization","profit"]:
    print(f"{k:20} base={s['summary'][k]:>10}  +barista={s2['summary'][k]:>10}")

# Sparse config like a messy upload: unknown roles, no demand, no inventory
sparse = {"cafe_name": "Messy", "operating_hours": [{"day_type":"weekday","open_hour":9,"close_hour":21}],
          "staff": [{"role":"employee","count":3}],
          "menu": [{"name":"Cappuccino","price":250},{"name":"Cold Coffee","price":250}]}
s3 = run_simulation(resolve(WorldConfig.model_validate(sparse)), seed=2)
print("SPARSE", s3["summary"]["orders_served"], s3["summary"]["revenue"], len(s3["timeseries"]))
for n in s3["assumptions_used"]: print(" -", n)
json.dumps(s3)  # must be serializable
print("serializable OK")
# reproducibility
a = run_simulation(resolve(base), seed=5)["summary"]; b = run_simulation(resolve(base), seed=5)["summary"]
print("reproducible:", a == b)