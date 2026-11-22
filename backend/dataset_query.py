import pandas as pd
from backend.dataset_loader import load_insurance_dataset



def search_policies(
    company=None,
    min_coverage=None,
    max_premium=None,
    cashless=None
):
    df = load_insurance_dataset()

    if company:
        df = df[
            df["Company"].str.contains(
                company, case=False, na=False
            )
        ]

    if min_coverage is not None:
        df = df[
            pd.to_numeric(df["Coverage_Amount"], errors="coerce")
            >= min_coverage
        ]

    if max_premium is not None:
        df = df[
            pd.to_numeric(df["Annual_Premium"], errors="coerce")
            <= max_premium
        ]

    if cashless is not None:
        df = df[
            df["Cashless_Available"].astype(str).str.lower()
            == str(cashless).lower()
        ]

    return df.to_dict(orient="records")


def compare_companies():
    df = load_insurance_dataset()

    numeric_columns = [
        "Annual_Premium",
        "Coverage_Amount",
        "Claim_Settlement_Ratio (%)",
        "Average_Claim_Processing_Time (in days)"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

    result = df.groupby("Company")[numeric_columns].mean()

    return result.round(2).reset_index().to_dict(
        orient="records"
    )


if __name__ == "__main__":
    import pandas as pd

    print("POLICY SEARCH:")
    print(search_policies(company="HDFC").__repr__()[:2000])

    print("\nCOMPANY COMPARISON:")
    print(compare_companies())
