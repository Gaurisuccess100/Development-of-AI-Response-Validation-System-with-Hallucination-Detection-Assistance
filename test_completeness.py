
from backend.rag.pipeline import answer_with_evidence
from backend.agents.completeness_agent import evaluate_completeness


question = (
    "What is the waiting period for pre-existing diseases "
    "under HDFC ERGO iCan Essential?"
)

# Intentionally incomplete answer for testing
answer = (
    "The waiting period for pre-existing diseases "
    "is 36 months of continuous coverage."
)

print("\nRetrieving policy evidence...")

retrieval = answer_with_evidence(question, top_k=30)
evidence = retrieval["evidence"]

print("Evidence retrieved:", len(evidence))

print("\nRunning Completeness Judge...")

try:
    result = evaluate_completeness(
        question=question,
        answer=answer,
        evidence=evidence
    )

    print("\nCOMPLETENESS JUDGE RESULT")
    print("-------------------------")

    for key, value in result.items():
        print(f"{key}: {value}")

except Exception as error:
    print("\nTesting failed:", error)
