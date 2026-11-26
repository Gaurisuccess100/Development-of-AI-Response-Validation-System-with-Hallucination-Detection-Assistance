
from backend.rag.pipeline import answer_with_evidence

from backend.dataset_query import (
    search_policies,
    compare_companies,
    get_dataset_summary,
    get_dataset_statistics
)

from backend.dataset_loader import load_insurance_dataset

import pandas as pd


# --------------------------------------------------
# KEYWORDS
# --------------------------------------------------

POLICY_KEYWORDS = [
    "waiting period",
    "pre existing disease",
    "pre-existing disease",
    "exclusion",
    "renewal",
    "claim conditions",
    "policy wording",
    "policy terms",
    "sum insured",
    "coverage condition",
    "cancer",
    "hospitalization",
    "policy clause",
    "plan",
    "plans",
    "different plans",
    "standard plan",
    "advanced plan",
    "benefits"
]


DATASET_KEYWORDS = [
    "premium",
    "coverage",
    "claim settlement",
    "claim processing",
    "cashless",
    "compare",
    "comparison",
    "insurance companies",
    "insurance company",
    "annual premium",
    "insurer",
    "dataset",
    "records",
    "record count",
    "how many",
    "number of",
    "average",
    "highest",
    "lowest",
    "maximum",
    "minimum",
    "fastest",
    "cheapest"
]


# --------------------------------------------------
# MAIN EVIDENCE RETRIEVER
# --------------------------------------------------

def retrieve_combined_evidence(question: str):

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    question_lower = question.lower()

    result = {
        "question": question,
        "pdf_evidence": [],
        "csv_evidence": [],
        "sources_used": []
    }

    # --------------------------------------------------
    # IDENTIFY COMPANY
    # --------------------------------------------------

    df = load_insurance_dataset()

    companies = (
        df["Company"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    matched_company = next(
        (
            company
            for company in companies
            if company.lower() in question_lower
        ),
        None
    )

    # --------------------------------------------------
    # IDENTIFY REQUIRED SOURCES
    # --------------------------------------------------

    needs_pdf = any(
        keyword in question_lower
        for keyword in POLICY_KEYWORDS
    )

    needs_csv = any(
        keyword in question_lower
        for keyword in DATASET_KEYWORDS
    )

    # --------------------------------------------------
    # PDF EVIDENCE
    # --------------------------------------------------

    if needs_pdf:

        try:

            pdf_result = answer_with_evidence(question)

            result["pdf_evidence"] = pdf_result.get(
                "evidence", []
            )

            if result["pdf_evidence"]:
                result["sources_used"].append("PDF")

        except Exception as e:

            result["pdf_error"] = str(e)

    # --------------------------------------------------
    # CSV EVIDENCE
    # --------------------------------------------------

    if needs_csv:

        try:

            csv_evidence = []

            # Complete dataset summary

            csv_evidence.append({
                "evidence_type": "Complete Dataset Summary",
                "data": get_dataset_summary()
            })

            # Overall dataset statistics

            csv_evidence.append({
                "evidence_type": "Dataset Statistics",
                "data": get_dataset_statistics()
            })

            # Company comparison

            is_comparison = any(
                word in question_lower
                for word in [
                    "compare",
                    "comparison",
                    "all companies"
                ]
            )

            if is_comparison:

                csv_evidence.append({
                    "evidence_type": "Company-wise Comparison",
                    "data": compare_companies()
                })

            else:

                # ------------------------------------------
                # DETECT REQUESTED METRIC
                # ------------------------------------------

                metric = None
                operation = None

                # Highest / lowest coverage

                if "coverage" in question_lower:

                    metric = "Coverage_Amount"

                    if any(
                        word in question_lower
                        for word in [
                            "lowest",
                            "minimum",
                            "smallest",
                            "least"
                        ]
                    ):
                        operation = "min"

                    else:
                        operation = "max"

                # Premium

                elif "premium" in question_lower:

                    metric = "Annual_Premium"

                    if any(
                        word in question_lower
                        for word in [
                            "lowest",
                            "minimum",
                            "cheapest",
                            "least"
                        ]
                    ):
                        operation = "min"

                    elif any(
                        word in question_lower
                        for word in [
                            "highest",
                            "maximum",
                            "costliest",
                            "most expensive"
                        ]
                    ):
                        operation = "max"

                # Claim settlement ratio

                elif "claim settlement" in question_lower:

                    metric = "Claim_Settlement_Ratio (%)"

                    if any(
                        word in question_lower
                        for word in [
                            "lowest",
                            "minimum",
                            "worst"
                        ]
                    ):
                        operation = "min"

                    else:
                        operation = "max"

                # Claim processing time

                elif "claim processing" in question_lower:

                    metric = "Average_Claim_Processing_Time (in days)"

                    if any(
                        word in question_lower
                        for word in [
                            "fastest",
                            "lowest",
                            "minimum",
                            "quickest"
                        ]
                    ):
                        operation = "min"

                    else:
                        operation = "max"

                # ------------------------------------------
                # CALCULATE ACTUAL EXTREMUM FROM FULL CSV
                # ------------------------------------------

                if metric and operation:

                    numeric_values = pd.to_numeric(
                        df[metric],
                        errors="coerce"
                    ).dropna()

                    if not numeric_values.empty:

                        if operation == "max":
                            selected_index = numeric_values.idxmax()

                        else:
                            selected_index = numeric_values.idxmin()

                        selected_record = (
                            df.loc[selected_index].to_dict()
                        )

                        csv_evidence.append({
                            "evidence_type": "Verified Extremum Record",
                            "metric": metric,
                            "operation": operation,
                            "data": selected_record
                        })

                # ------------------------------------------
                # COMPANY-SPECIFIC POLICY QUESTIONS
                # ------------------------------------------

                elif matched_company:

                    policy_results = search_policies(
                        company=matched_company
                    )

                    csv_evidence.append({
                        "evidence_type": "Company Policy Records",
                        "company": matched_company,
                        "data": policy_results[:10]
                    })

                # ------------------------------------------
                # GENERAL POLICY QUESTIONS
                # ------------------------------------------

                else:

                    question_needs_policy_records = any(
                        word in question_lower
                        for word in [
                            "policy",
                            "policies",
                            "product",
                            "which policy",
                            "which insurer",
                            "which company"
                        ]
                    )

                    if question_needs_policy_records:

                        policy_results = search_policies()

                        csv_evidence.append({
                            "evidence_type": "Policy Records",
                            "data": policy_results[:10]
                        })

            # Store CSV evidence

            result["csv_evidence"] = csv_evidence

            if csv_evidence:
                result["sources_used"].append("CSV")

        except Exception as e:

            result["csv_error"] = str(e)

    # --------------------------------------------------
    # RETURN FINAL RESULT
    # --------------------------------------------------

    return result


# --------------------------------------------------
# TESTING
# --------------------------------------------------

if __name__ == "__main__":

    test_questions = [

        "How many records are in the insurance dataset?",

        "How many insurance companies are present?",

        "Compare HDFC ERGO with other insurance companies on premium and claim settlement ratio.",

        "What is the waiting period in HDFC iCan Essential?",

        "Compare insurance premiums and explain the policy waiting period.",

        "Which policy offers the highest coverage?",

        "Which policy has the lowest premium?",

        "Which company has the highest claim settlement ratio?",

        "Which company has the fastest claim processing?"
    ]

    for question in test_questions:

        print("\n" + "=" * 60)

        print("QUESTION:", question)

        evidence = retrieve_combined_evidence(question)

        print("SOURCES:", evidence["sources_used"])

        print(
            "PDF RECORDS:",
            len(evidence["pdf_evidence"])
        )

        print(
            "CSV EVIDENCE ITEMS:",
            len(evidence["csv_evidence"])
        )

        if "csv_error" in evidence:
            print("CSV ERROR:", evidence["csv_error"])

        if "pdf_error" in evidence:
            print("PDF ERROR:", evidence["pdf_error"])

        for item in evidence["csv_evidence"]:

            print("\nCSV EVIDENCE TYPE:", item["evidence_type"])

            if item["evidence_type"] in [
                "Complete Dataset Summary",
                "Verified Extremum Record"
            ]:
                print(item["data"])
