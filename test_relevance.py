
from backend.agents.relevance_agent import evaluate_relevance

question = "What is the waiting period for pre-existing diseases?"

answer = (
    "The waiting period for pre-existing diseases "
    "is 36 months of continuous coverage."
)

try:
    result = evaluate_relevance(question, answer)

    print("\nRELEVANCE AGENT RESULT")
    print("----------------------")

    for key, value in result.items():
        print(f"{key}: {value}")

except Exception as error:
    print("Agent testing failed:", error)
