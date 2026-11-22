
from backend.rag.pipeline import answer_with_evidence
from backend.dataset_query import search_policies, compare_companies
from backend.dataset_loader import load_insurance_dataset


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
    "policy clause"
]

DATASET_KEYWORDS = [
    "premium",
    "coverage amount",
    "claim settlement",
    "claim processing",
    "cashless",
    "compare",
    "comparison",
    "insurance companies",
    "insurance company",
    "annual premium",
    "insurer",
    "dataset"
]


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

    # Identify companies
    df = load_insurance_dataset()
    companies = df["Company"].dropna().unique().tolist()

    matched_company = next(
        (
            company for company in companies
            if company.lower() in question_lower
        ),
        None
    )

    # Identify source requirements
    needs_pdf = any(
        keyword in question_lower
        for keyword in POLICY_KEYWORDS
    )
    needs_csv = any(
    keyword in question_lower
    for keyword in DATASET_KEYWORDS
)




    # Retrieve PDF evidence only for policy-related questions
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

    # Retrieve CSV evidence for dataset-related questions
    if needs_csv:
        try:
            is_comparison = any(
                word in question_lower
                for word in ["compare", "comparison", "all companies"]
            )

            if is_comparison:
                csv_result = compare_companies()
            else:
                csv_result = search_policies(
                    company=matched_company
                )

            result["csv_evidence"] = csv_result[:10]

            if result["csv_evidence"]:
                result["sources_used"].append("CSV")

        except Exception as e:
            result["csv_error"] = str(e)

    return result


if __name__ == "__main__":

    test_questions = [
        "Compare HDFC ERGO with other insurance companies on premium and claim settlement ratio.",
        "What is the waiting period in HDFC iCan Essential?",
        "Compare insurance premiums and explain the policy waiting period."
    ]

    for question in test_questions:

        print("\nQUESTION:", question)

        evidence = retrieve_combined_evidence(question)

        print("SOURCES:", evidence["sources_used"])
        print("PDF RECORDS:", len(evidence["pdf_evidence"]))
        print("CSV RECORDS:", len(evidence["csv_evidence"]))
