
import json
import re

from backend.agents.llm_client import ask_groq


def evaluate_completeness(question, answer, evidence):

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not answer or not answer.strip():
        raise ValueError("Answer cannot be empty.")

    if not evidence:
        return {
            "agent": "Completeness Judge",
            "score": None,
            "verdict": "Insufficient Evidence",
            "missing_information": [],
            "explanation": "No evidence was provided."
        }

    evidence_items = []

    for item in evidence:

        if isinstance(item, dict):

            source = item.get("source", "Unknown")
            page = item.get("page", "Unknown")
            text = item.get("text", "")

            if text:
                evidence_items.append(
                    f"Source: {source}\n"
                    f"Page/Record: {page}\n"
                    f"Evidence: {text}"
                )

        elif isinstance(item, str):
            evidence_items.append(item)

    if not evidence_items:
        return {
            "agent": "Completeness Judge",
            "score": None,
            "verdict": "Insufficient Evidence",
            "missing_information": [],
            "explanation": "No usable evidence was available."
        }

    evidence_text = "\n\n".join(evidence_items)

    prompt = f"""
You are a Completeness Judge in an AI Response
Validation System.

Your task is to evaluate whether an AI-generated answer
contains all important information needed to answer
the user's question.

USER QUESTION:
{question}

AI-GENERATED ANSWER:
{answer}

REFERENCE EVIDENCE:
{evidence_text}

GENERAL COMPLETENESS RULES:

1. Check whether the answer addresses every part
   of the user's question.

2. Identify important missing conditions,
   exceptions, limitations and context.

3. Check whether the answer is sufficiently specific.

4. Do not penalize omission of irrelevant details.

5. Do not invent missing information.

6. Evaluate completeness, not factual accuracy.
   Other agents handle factual correctness.

7. A concise answer can receive a high score
   if it contains all information necessary
   to answer the question.

CSV DATASET COMPLETENESS RULES:

When evidence contains insurance CSV records:

1. Identify the exact company and policy product
   relevant to the question.

2. Check whether multiple records exist for
   the same company and product.

3. If multiple matching records contain different
   premiums or coverage amounts, check whether
   the answer clarifies which record it refers to.

4. If the answer gives one record's values without
   explaining that they belong to a specific record,
   identify the missing record-level context.

5. If the question asks for a comparison,
   check whether the answer compares the requested
   companies or relevant fields.

6. Do not require every dataset field in the answer.
   Include only fields relevant to the question.

7. If the answer uses sample dataset figures,
   it should not imply that they are universal
   real-world quotations.

8. Do not assume why premiums differ unless
   the evidence explicitly establishes the reason.

PDF POLICY COMPLETENESS RULES:

When evidence contains PDF policy documents:

1. Check whether the answer includes the relevant
   waiting period, conditions and exclusions.

2. Check whether important exceptions or eligibility
   conditions are omitted.

3. If the evidence specifies a condition such as
   continuous coverage, evaluate whether it is
   necessary to include it in the answer.

4. Do not require unrelated policy clauses.

MIXED PDF AND CSV QUESTIONS:

If the question requires information from both sources,
check whether the answer addresses both sources.

Do not penalize the answer for information that
is not relevant to the question.

SCORING:

9-10: Fully complete; all important requested
information and necessary context are included.

7-8: Mostly complete; only minor context is missing.

4-6: Partially complete; an important condition,
limitation or clarification is missing.

0-3: Highly incomplete; major parts of the question
are unanswered.

Return ONLY valid JSON:

{{
    "score": 0,
    "verdict": "Incomplete",
    "missing_information": [],
    "explanation": "Explain your evaluation."
}}

Rules:
- Score must be between 0 and 10.
- Verdict must be "Complete", "Partially Complete",
  or "Incomplete".
- 10 means fully complete.
- 0 means highly incomplete.
- Do not evaluate factual accuracy.
- Do not invent missing information.
"""

    response = ask_groq(
        prompt,
        system_prompt=(
            "You are a careful AI response completeness evaluator. "
            "Distinguish missing context from factual errors. "
            "Consider PDF policy conditions and CSV record-level "
            "ambiguity when relevant. Return valid JSON only."
        )
    )

    try:

        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:
            raise ValueError("No JSON object found.")

        result = json.loads(match.group())

        score = result.get("score")

        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not 0 <= score <= 10
        ):
            raise ValueError("Invalid completeness score.")

        allowed_verdicts = [
            "Complete",
            "Partially Complete",
            "Incomplete"
        ]

        if result.get("verdict") not in allowed_verdicts:
            raise ValueError("Invalid completeness verdict.")

        if not isinstance(result.get("missing_information"), list):
            raise ValueError("Invalid missing information.")

        if not isinstance(result.get("explanation"), str):
            raise ValueError("Invalid explanation.")

        return {
            "agent": "Completeness Judge",
            "score": score,
            "verdict": result["verdict"],
            "missing_information": result["missing_information"],
            "explanation": result["explanation"]
        }

    except (json.JSONDecodeError, ValueError) as error:

        raise RuntimeError(
            f"Completeness evaluation failed: {error}. "
            f"Model response: {response}"
        )
