import pandas as pd


def parse_csv(file_path: str) -> dict:
    df = pd.read_csv(file_path)

    return {
        "columns": df.columns.tolist(),
        "row_count": len(df),
        "rows": df.to_dict(orient="records"),
    }