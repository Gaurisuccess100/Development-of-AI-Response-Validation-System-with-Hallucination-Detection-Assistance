
from backend.rag.pipeline import answer_with_evidence
from backend.agents.hallucination_agent import detect_hallucinations


question = (
    "What is the waiting period for pre-existing diseases "
    "under HDFC ERGO iCan Essential?"
)

answer = (
    "The waiting period for pre-existing diseases is "
    "12 months of continuous coverage."
)

retrieval = answer_with_evidence(question, top_k=30)
evidence = retrieval["evidence"]

print("\nEvidence retrieved:", len(evidence))

print("\nRunning Hallucination Detection Agent...")

try:
    result = detect_hallucinations(
        question=question,
        answer=answer,
        evidence=evidence
    )

    print("\nHALLUCINATION DETECTION RESULT")
    print("------------------------------")

    for key, value in result.items():
        print(f"{key}: {value}")

except Exception as error:
    print("Testing failed:", error)
