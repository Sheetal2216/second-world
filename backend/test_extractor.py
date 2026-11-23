
from sqlalchemy import select

from core.database import SessionLocal
from models.dataset_db import DatasetDB
from ai.extractor import generate_world_config


def main():
    with SessionLocal() as db:
        statement = (
            select(DatasetDB)
            .where(
                DatasetDB.status == "processed",
                DatasetDB.parsed_data.is_not(None),
            )
            .order_by(DatasetDB.created_at.desc())
            .limit(5)
        )

        datasets = db.scalars(statement).all()

    if not datasets:
        print("No processed datasets found in the database.")
        return

    print(f"Found {len(datasets)} processed dataset(s).")
    print("Sending café data to Gemini...")

    config = generate_world_config(datasets)

    print("\nSUCCESS! WorldConfig generated and validated.")
    print("Cafe:", config.cafe_name)
    print("Menu items:", len(config.menu))
    print("Staff roles:", len(config.staff))
    print("Operating hour entries:", len(config.operating_hours))
    print("Source dataset IDs:", config.source_dataset_ids)
    print("Assumptions:", len(config.assumptions))
    print("Missing information entries:", len(config.missing_information))

    print("\nGenerated configuration:")
    print(config.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
