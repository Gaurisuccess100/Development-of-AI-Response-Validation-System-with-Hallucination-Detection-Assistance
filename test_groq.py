
from backend.agents.llm_client import ask_groq

try:
    result = ask_groq(
        "Explain what hallucination means in AI in two sentences."
    )

    print("\nGroq connection successful!")
    print("\nAI Response:")
    print(result)

except Exception as error:
    print("\nGroq connection failed.")
    print("Error:", error)
