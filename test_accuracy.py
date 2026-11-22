
from backend.rag.pipeline import answer_with_evidence
from backend.agents.accuracy_agent import evaluate_accuracy


question = (
    "What is the waiting period for pre-existing diseases "
    "under HDFC ERGO iCan Essential?"
)

answer = (
    "The waiting period for pre-existing diseases is "
    "36 months of continuous coverage. After 36 months, "
    "coverage is subject to policy conditions, declaration "
    "and insurer acceptance."
)

print("\nRetrieving policy evidence...")

retrieval = answer_with_evidence(question, top_k=30)
evidence = retrieval["evidence"]

print("Evidence retrieved:", len(evidence))

for item in evidence:
    if (
        "36 months of continuous coverage" in item["text"].lower()
        and "pre-existing disease" in item["text"].lower()
    ):
        print("Exact PED clause found on page:", item["page"])
        break

print("\nRunning Accuracy Judge...")

try:
    result = evaluate_accuracy(
        question=question,
        answer=answer,
        evidence=evidence
    )

    print("\nACCURACY JUDGE RESULT")
    print("---------------------")

    for key, value in result.items():
        print(f"{key}: {value}")

except Exception as error:
    print("\nAccuracy evaluation failed:", error)
