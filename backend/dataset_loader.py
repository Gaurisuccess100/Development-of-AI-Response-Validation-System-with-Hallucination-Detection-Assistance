
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "backend" / "uploads" / "insurance_dataset.csv"


def load_insurance_dataset():
    """Load and validate the insurance dataset."""

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Insurance dataset not found: {CSV_PATH}"
        )

    df = pd.read_csv(CSV_PATH)

    if df.empty:
        raise ValueError("Insurance dataset is empty.")

    df.columns = df.columns.str.strip()

    return df


def get_dataset_summary():
    df = load_insurance_dataset()

    return {
        "total_records": len(df),
        "total_columns": len(df.columns),
        "columns": df.columns.tolist(),
        "companies": sorted(
            df["Company"].dropna().unique().tolist()
        )
    }


if __name__ == "__main__":
    print(get_dataset_summary())
