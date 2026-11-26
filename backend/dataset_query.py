
import pandas as pd
from pathlib import Path


# --------------------------------------------------
# LOAD INSURANCE DATASET
# --------------------------------------------------

DATASET_PATH = (
    Path(__file__).resolve().parent
    / "uploads"
    / "insurance_dataset.csv"
)


def load_insurance_dataset():
    """
    Loads the insurance CSV dataset.
    Expected location: backend/insurance_dataset.csv
    """

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Insurance dataset not found: {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    if df.empty:
        raise ValueError("Insurance dataset is empty.")

    return df


# --------------------------------------------------
# DATASET SUMMARY
# --------------------------------------------------

def get_dataset_summary():
    """
    Returns complete dataset information,
    including the total number of companies.
    """

    df = load_insurance_dataset()

    companies = sorted(
        df["Company"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    return {
        "total_records": int(len(df)),
        "total_companies": len(companies),
        "companies": companies
    }


# --------------------------------------------------
# SEARCH INSURANCE POLICIES
# --------------------------------------------------

def search_policies(
    company=None,
    min_coverage=None,
    max_premium=None,
    cashless=None
):
    """
    Search insurance policies using optional filters.
    """

    df = load_insurance_dataset()

    if company:
        df = df[
            df["Company"].astype(str).str.contains(
                company,
                case=False,
                na=False
            )
        ]

    if min_coverage is not None:
        coverage = pd.to_numeric(
            df["Coverage_Amount"],
            errors="coerce"
        )

        df = df[coverage >= min_coverage]

    if max_premium is not None:
        premium = pd.to_numeric(
            df["Annual_Premium"],
            errors="coerce"
        )

        df = df[premium <= max_premium]

    if cashless is not None:
        df = df[
            df["Cashless_Available"]
            .astype(str)
            .str.strip()
            .str.lower()
            == str(cashless).strip().lower()
        ]

    return df.to_dict(orient="records")


# --------------------------------------------------
# COMPANY-WISE COMPARISON
# --------------------------------------------------

def compare_companies():
    """
    Calculates average premium, coverage,
    claim settlement ratio and processing time
    for every company in the complete dataset.
    """

    df = load_insurance_dataset()

    numeric_columns = [
        "Annual_Premium",
        "Coverage_Amount",
        "Claim_Settlement_Ratio (%)",
        "Average_Claim_Processing_Time (in days)"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    result = (
        df.groupby("Company")[numeric_columns]
        .mean()
        .round(2)
        .reset_index()
    )

    return result.to_dict(orient="records")


# --------------------------------------------------
# DATASET STATISTICS
# --------------------------------------------------

def get_dataset_statistics():
    """
    Returns useful overall statistics from the dataset.
    """

    df = load_insurance_dataset()

    numeric_columns = [
        "Annual_Premium",
        "Coverage_Amount",
        "Claim_Settlement_Ratio (%)",
        "Average_Claim_Processing_Time (in days)"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return {
        "total_records": int(len(df)),
        "total_companies": int(
            df["Company"].nunique()
        ),
        "average_annual_premium": round(
            float(df["Annual_Premium"].mean()), 2
        ),
        "average_coverage": round(
            float(df["Coverage_Amount"].mean()), 2
        ),
        "average_claim_settlement_ratio": round(
            float(
                df["Claim_Settlement_Ratio (%)"].mean()
            ), 2
        ),
        "average_claim_processing_days": round(
            float(
                df[
                    "Average_Claim_Processing_Time (in days)"
                ].mean()
            ), 2
        )
    }


# --------------------------------------------------
# TEST THE FUNCTIONS
# --------------------------------------------------

if __name__ == "__main__":

    print("\n========== DATASET SUMMARY ==========")
    print(get_dataset_summary())

    print("\n========== DATASET STATISTICS ==========")
    print(get_dataset_statistics())

    print("\n========== POLICY SEARCH ==========")
    policies = search_policies(company="HDFC")

    for policy in policies[:5]:
        print(policy)

    print("\n========== COMPANY COMPARISON ==========")
    for company in compare_companies():
        print(company)
