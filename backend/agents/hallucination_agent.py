
import json
import re

from backend.agents.llm_client import ask_groq


def detect_hallucinations(question, answer, evidence):

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not answer or not answer.strip():
        raise ValueError("Answer cannot be empty.")

    if not evidence:
        return {
            "agent": "Hallucination Detection Agent",
            "hallucination_detected": None,
            "verdict": "Insufficient Evidence",
            "hallucinated_claims": [],
            "supported_claims": [],
            "explanation": "No evidence was provided for verification."
        }

    evidence_text = []

    for item in evidence:

        if isinstance(item, dict):

            text = item.get("text", "")
            source = item.get("source", "Unknown")
            page = item.get("page", "Unknown")

            if text:
                evidence_text.append(
                    f"Source: {source}, Page: {page}\n{text}"
                )

        elif isinstance(item, str):
            evidence_text.append(item)

    if not evidence_text:
        return {
            "agent": "Hallucination Detection Agent",
            "hallucination_detected": None,
            "verdict": "Insufficient Evidence",
            "hallucinated_claims": [],
            "supported_claims": [],
            "explanation": "No usable evidence was available."
        }

    combined_evidence = "\n\n".join(evidence_text)

    prompt = f"""
You are a strict Hallucination Detection Agent
in an AI Response Validation System.

Your task is to identify factual claims in an
AI-generated answer that are unsupported,
contradicted, fabricated, or misleading
when compared with the supplied evidence.

USER QUESTION:
{question}

AI-GENERATED ANSWER:
{answer}

AVAILABLE EVIDENCE:
{combined_evidence}

GENERAL RULES:

1. Evaluate every important factual claim.
2. Use only the supplied evidence.
3. Never use outside knowledge.
4. Do not invent facts.
5. Distinguish supported, unsupported and contradicted claims.
6. Missing information alone does not prove hallucination.
7. Do not confuse different companies or policy products.
8. Verify numerical values carefully.

CSV DATASET RULES:

When evidence contains insurance CSV records:

1. Treat every record as a separate policy record.

2. Match the exact company and policy product
   mentioned in the question.

3. Verify numerical claims against the corresponding
   record, including premium, coverage amount,
   settlement ratio and processing time.

4. A value matching one record is supported
   for that record only.

5. If multiple records for the same company and
   product contain different values, identify
   whether the answer incorrectly presents one
   value as universal.

6. Do not label a claim as fabricated merely because
   another record has a different value.

7. If a value matches one record but the answer
   implies it applies to every policy, explain
   the ambiguity and classify it appropriately.

8. If a claim is explicitly contradicted by the
   matching evidence, identify it as hallucinated.

9. Distinguish sample dataset figures from
   verified real-world quotations.

10. Do not infer causal relationships between
    fields unless the evidence establishes them.

PDF POLICY RULES:

1. Verify policy conditions using supplied PDF evidence.
2. Check waiting periods, exclusions and exceptions.
3. Do not confuse different policy conditions.
4. Identify invented policy rules or incorrect
   interpretations of the supplied clauses.

IMPORTANT DISTINCTION:

- Supported: Directly supported by evidence.
- Unsupported: Evidence does not establish the claim.
- Contradicted: Evidence directly conflicts with the claim.
- Ambiguous: Claim matches some records but is
  presented too broadly or without necessary context.

A merely incomplete answer is not automatically
a hallucination.

If no reliable evidence is available, use
"Insufficient Evidence".

Return ONLY valid JSON:

{{
    "hallucination_detected": false,
    "verdict": "No Hallucination",
    "supported_claims": [],
    "hallucinated_claims": [],
    "explanation": "Explain the result."
}}

Allowed verdicts:
- No Hallucination
- Hallucination Detected
- Insufficient Evidence

hallucination_detected must be true, false, or null.
"""

    response = ask_groq(
        prompt,
        system_prompt=(
            "You are a careful factual verification agent. "
            "Check claims against individual evidence records. "
            "Distinguish unsupported claims from contradicted claims "
            "and avoid treating one matching record as universal. "
            "Never use outside knowledge. Return valid JSON only."
        )
    )

    try:

        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:
            raise ValueError("No JSON object found.")

        result = json.loads(match.group())

        allowed_verdicts = [
            "No Hallucination",
            "Hallucination Detected",
            "Insufficient Evidence"
        ]

        if result.get("verdict") not in allowed_verdicts:
            raise ValueError("Invalid verdict.")

        detected = result.get("hallucination_detected")

        if detected not in (True, False, None):
            raise ValueError("Invalid hallucination status.")

        if not isinstance(result.get("supported_claims"), list):
            raise ValueError("Invalid supported claims.")

        if not isinstance(result.get("hallucinated_claims"), list):
            raise ValueError("Invalid hallucinated claims.")

        if not isinstance(result.get("explanation"), str):
            raise ValueError("Invalid explanation.")

        # Ensure verdict and status remain consistent.
        if result["verdict"] == "Hallucination Detected":
            if detected is not True:
                raise ValueError("Inconsistent hallucination status.")

        elif result["verdict"] == "No Hallucination":
            if detected is not False:
                raise ValueError("Inconsistent hallucination status.")

        elif result["verdict"] == "Insufficient Evidence":
            if detected is not None:
                raise ValueError("Inconsistent hallucination status.")

        return {
            "agent": "Hallucination Detection Agent",
            "hallucination_detected": detected,
            "verdict": result["verdict"],
            "supported_claims": result["supported_claims"],
            "hallucinated_claims": result["hallucinated_claims"],
            "explanation": result["explanation"]
        }

    except (json.JSONDecodeError, ValueError) as error:

        raise RuntimeError(
            f"Hallucination detection failed: {error}. "
            f"Model response: {response}"
        )
