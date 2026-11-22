
from backend.rag.pipeline import answer_with_evidence

from backend.agents.relevance_agent import evaluate_relevance
from backend.agents.accuracy_agent import evaluate_accuracy
from backend.agents.hallucination_agent import detect_hallucinations
from backend.agents.completeness_agent import evaluate_completeness
from backend.agents.verdict_agent import generate_final_verdict


question = (
    "What is the waiting period for pre-existing diseases "
    "under HDFC ERGO iCan Essential?"
)

answer = (
    "The waiting period for pre-existing diseases is "
    "36 months of continuous coverage. After 36 months, "
    "coverage is subject to declaration and insurer acceptance."
)


print("\nSTEP 1: RETRIEVING EVIDENCE")

retrieval = answer_with_evidence(question, top_k=30)

# Pass only the top 5 relevant chunks to LLM agents
evidence = retrieval["evidence"][:5]

print("Evidence retrieved:", len(evidence))


print("\nSTEP 2: RUNNING RELEVANCE JUDGE")

relevance_result = evaluate_relevance(question, answer)
print(relevance_result)


print("\nSTEP 3: RUNNING ACCURACY JUDGE")

accuracy_result = evaluate_accuracy(
    question=question,
    answer=answer,
    evidence=evidence
)
print(accuracy_result)


print("\nSTEP 4: RUNNING HALLUCINATION DETECTION")

hallucination_result = detect_hallucinations(
    question=question,
    answer=answer,
    evidence=evidence
)
print(hallucination_result)


print("\nSTEP 5: RUNNING COMPLETENESS JUDGE")

completeness_result = evaluate_completeness(
    question=question,
    answer=answer,
    evidence=evidence
)
print(completeness_result)


print("\nSTEP 6: GENERATING FINAL VERDICT")

try:
    final_result = generate_final_verdict(
        question=question,
        answer=answer,
        relevance_result=relevance_result,
        accuracy_result=accuracy_result,
        hallucination_result=hallucination_result,
        completeness_result=completeness_result
    )

    print("\n========== FINAL EVALUATION ==========")

    for key, value in final_result.items():
        print(f"{key}: {value}")

    print("\n========== TEST COMPLETED ==========")

except Exception as error:
    print("Final verdict testing failed:", error)
