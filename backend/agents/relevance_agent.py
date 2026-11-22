
import json
import re

from backend.agents.llm_client import ask_groq


def evaluate_relevance(question, answer):

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not answer or not answer.strip():
        raise ValueError("Answer cannot be empty.")

    prompt = f"""
You are a Relevance Judge in an AI Response
Validation System.

Your task is to evaluate whether an AI-generated
answer is relevant to the user's question.

USER QUESTION:
{question}

AI-GENERATED ANSWER:
{answer}

Evaluate relevance only.
Do not evaluate factual accuracy.

Return ONLY a valid JSON object in this format:

{{
    "score": 0,
    "verdict": "Relevant",
    "explanation": "Explain your evaluation."
}}

Rules:
- Score must be between 0 and 10.
- 0 means completely irrelevant.
- 10 means directly relevant.
- Verdict must be "Relevant", "Partially Relevant",
  or "Not Relevant".
- Give a short, clear explanation.
"""

    response = ask_groq(
        prompt,
        system_prompt=(
            "You are a careful AI response relevance evaluator. "
            "Return valid JSON only."
        )
    )

    try:
        # Extract JSON if the model adds extra text
        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:
            raise ValueError("No JSON object found.")

        result = json.loads(match.group())

        score = result.get("score")

        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("Invalid relevance score.")

        if not 0 <= score <= 10:
            raise ValueError("Score must be between 0 and 10.")

        allowed_verdicts = [
            "Relevant",
            "Partially Relevant",
            "Not Relevant"
        ]

        if result.get("verdict") not in allowed_verdicts:
            raise ValueError("Invalid relevance verdict.")

        if not isinstance(result.get("explanation"), str):
            raise ValueError("Invalid explanation.")

        return {
            "agent": "Relevance Judge",
            "score": score,
            "verdict": result["verdict"],
            "explanation": result["explanation"]
        }

    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(
            f"Relevance evaluation failed: {error}. "
            f"Model response: {response}"
        )
