
from pydantic import ValidationError
from schemas.world import WorldConfig

example = {
    "cafe_name": "Brew & Bites",
    "seating_capacity": 24,
    "operating_hours": [
        {
            "day_type": "weekday",
            "open_hour": 8,
            "close_hour": 22,
        },
        {
            "day_type": "weekend",
            "open_hour": 9,
            "close_hour": 23,
        },
    ],
    "staff": [
        {
            "role": "barista",
            "count": 2,
            "hourly_wage": 120,
            "duties": "preparation",
        },
        {
            "role": "cashier",
            "count": 1,
            "hourly_wage": 100,
            "duties": "order_taking",
        },
    ],
    "menu": [
        {
            "name": "Cappuccino",
            "price": 160,
            "unit_cost": 45,
            "prep_time_seconds": 150,
            "popularity_share": 0.5,
            "ingredients": [
                {"ingredient": "milk", "quantity": 150},
                {"ingredient": "coffee beans", "quantity": 18},
            ],
        },
        {
            "name": "Veg Sandwich",
            "price": 140,
            "unit_cost": 50,
            "prep_time_seconds": 240,
            "popularity_share": 0.5,
            "ingredients": [
                {"ingredient": "bread", "quantity": 2},
            ],
        },
    ],
    "inventory": [
        {
            "ingredient": "milk",
            "unit": "ml",
            "starting_quantity": 20000,
        },
        {
            "ingredient": "coffee beans",
            "unit": "g",
            "starting_quantity": 3000,
        },
        {
            "ingredient": "bread",
            "unit": "pcs",
            "starting_quantity": 60,
        },
    ],
    "demand": [
        {
            "day_type": "weekday",
            "hour": hour,
            "avg_arrivals": arrivals,
        }
        for hour, arrivals in [
            (8, 10),
            (9, 18),
            (12, 25),
            (18, 30),
            (20, 22),
        ]
    ],
    "demand_modifiers": [
        {
            "description": "Weekend evening rush",
            "day_type": "weekend",
            "start_hour": 18,
            "end_hour": 21,
            "multiplier": 1.3,
        }
    ],
    "customer_behavior": {
        "avg_patience_minutes": None,
    },
    "assumptions": [
        {
            "field_path": "menu[1].prep_time_seconds",
            "assumed_value": "240",
            "reason": "Illustrative sandwich preparation estimate.",
        }
    ],
    "missing_information": [
        {
            "field_path": "customer_behavior.avg_patience_minutes",
            "why_needed": "Needed to model customers leaving long queues.",
        }
    ],
    "source_dataset_ids": [3, 4, 5],
}

# Test 1: Valid configuration
config = WorldConfig.model_validate(example)

print("VALID CONFIG:", config.cafe_name)
print("Menu items:", len(config.menu))
print("Assumptions:", len(config.assumptions))
print("Missing information:", len(config.missing_information))

# Test 2: Invalid opening hours must be rejected
bad_example = {
    **example,
    "operating_hours": [
        {
            "day_type": "weekday",
            "open_hour": 22,
            "close_hour": 8,
        }
    ],
}

try:
    WorldConfig.model_validate(bad_example)
except ValidationError:
    print("INVALID HOURS: correctly rejected")
else:
    raise AssertionError("Invalid opening hours were accepted")

# Test 3: Duplicate menu names must be rejected
duplicate_example = {
    **example,
    "menu": [
        {"name": "Coffee", "price": 100},
        {"name": "coffee", "price": 120},
    ],
}

try:
    WorldConfig.model_validate(duplicate_example)
except ValidationError:
    print("DUPLICATE MENU: correctly rejected")
else:
    raise AssertionError("Duplicate menu names were accepted")

# Test 4: Generate the JSON schema for a future AI prompt
schema = WorldConfig.model_json_schema()
print("JSON SCHEMA GENERATED:", "properties" in schema)

# Export validated config as JSON
print("CONFIG JSON:")
print(config.model_dump_json(indent=2))
