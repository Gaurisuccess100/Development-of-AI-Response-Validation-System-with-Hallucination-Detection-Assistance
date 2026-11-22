
import json
import re


from backend.agents.llm_client import ask_groq


def extract_json_records(evidence):
    """Extract CSV-style JSON records from retrieved evidence."""

    records = []
    decoder = json.JSONDecoder()

    for item in evidence:
        if isinstance(item, dict):
            text = item.get("text", "")

            # Evidence may itself contain a structured record.
            if "Annual_Premium" in item and "Coverage_Amount" in item:
                records.append(item)

        elif isinstance(item, str):
            text = item

        else:
            continue

        if not text:
            continue

        # Find JSON objects embedded in the evidence text.
        for match in re.finditer(r"\{", text):
            try:
                record, _ = decoder.raw_decode(text[match.start():])

                if (
                    isinstance(record, dict)
                    and "Annual_Premium" in record
                    and "Coverage_Amount" in record
                ):
                    records.append(record)

            except json.JSONDecodeError:
                continue

    # Remove duplicate records.
    unique_records = {}

    for record in records:
        policy_id = record.get("Policy_ID")

        if policy_id:
            unique_records[policy_id] = record
        else:
            unique_records[str(record)] = record

    return list(unique_records.values())


def to_number(value):
    """Convert a numeric value into a float safely."""

    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def validate_csv_numerical_claims(question, answer, evidence):
    """
    Compare explicitly labelled annual premium and coverage
    values in the answer against the same CSV evidence record.
    """

    records = extract_json_records(evidence)

    if not records:
        return []

    question_lower = question.lower()

    # Narrow records to the product named in the question.
    if "platinum mediclaim" in question_lower:
        records = [
            record for record in records
            if "platinum mediclaim" in str(
                record.get("Policy_Product", "")
            ).lower()
        ]

    if "hdfc ergo" in question_lower:
        records = [
            record for record in records
            if "hdfc ergo" in str(
                record.get("Company", "")
            ).lower()
        ]

    if not records:
        return []

    evidence_pairs = []

    for record in records:
        premium = to_number(record.get("Annual_Premium"))
        coverage = to_number(record.get("Coverage_Amount"))

        if premium is not None and coverage is not None:
            evidence_pairs.append({
                "premium": premium,
                "coverage": coverage,
                "policy_id": record.get("Policy_ID", "Unknown")
            })

    if not evidence_pairs:
        return []

    # Extract premium and coverage values from the same answer line.
    premium_pattern = re.compile(
        r"annual\s+premium\s*[:=]\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE
    )

    coverage_pattern = re.compile(
        r"coverage(?:\s+amount)?\s*[:=]\s*([\d,]+(?:\.\d+)?)",
        re.IGNORECASE
    )

    contradictions = []

    for line in answer.splitlines():
        premium_match = premium_pattern.search(line)
        coverage_match = coverage_pattern.search(line)

        if not premium_match or not coverage_match:
            continue

        answer_premium = to_number(premium_match.group(1))
        answer_coverage = to_number(coverage_match.group(1))

        if answer_premium is None or answer_coverage is None:
            continue

        # Find evidence records with the same annual premium.
        matching_premium_records = [
            record for record in evidence_pairs
            if record["premium"] == answer_premium
        ]

        if not matching_premium_records:
            continue

        # Check whether the premium and coverage belong together.
        exact_pair_found = any(
            record["coverage"] == answer_coverage
            for record in matching_premium_records
        )

        if not exact_pair_found:
            correct_coverages = [
                record["coverage"]
                for record in matching_premium_records
            ]

            contradictions.append(
                f"Annual premium {answer_premium:g} is associated "
                f"with coverage amount {answer_coverage:g} in the "
                f"answer, but the supplied CSV evidence associates "
                f"that premium with coverage amount(s) "
                f"{correct_coverages}."
            )

    return contradictions


def evaluate_accuracy(question, answer, evidence):

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not answer or not answer.strip():
        raise ValueError("Answer cannot be empty.")

    if not evidence:
        raise ValueError(
            "Evidence is required for accuracy evaluation."
        )

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
        raise ValueError("No usable evidence found.")

    combined_evidence = "\n\n".join(evidence_text)

    prompt = f"""
You are a strict and reliable Accuracy Judge
in an AI Response Validation System.

Your task is to evaluate whether the AI-generated
answer is factually supported by the supplied evidence.

USER QUESTION:
{question}

AI-GENERATED ANSWER:
{answer}

RETRIEVED EVIDENCE:
{combined_evidence}

GENERAL RULES:

1. Use ONLY the supplied evidence.
2. Never use outside knowledge.
3. Identify supported, unsupported and contradicted claims.
4. Missing evidence does not automatically mean a claim is false.
5. Do not confuse different companies or policy products.
6. Preserve numerical values and their units accurately.
7. Do not assume relationships or causes not established by evidence.

IMPORTANT CSV DATASET RULES:

1. Treat every CSV record as a separate policy record.
2. Match the company and policy product mentioned in the question.
3. Verify every numerical claim individually.
4. Compare annual premium and coverage amount together
   against the SAME evidence record.
5. Never combine the premium from one record with
   the coverage amount from another record.
6. A correct value in three records does not make
   a fourth incorrect value correct.
7. If even one explicitly stated numerical value contradicts
   the evidence, identify that specific claim as contradicted.
8. Do not award a fully correct score when an important
   numerical claim is contradicted.
9. If multiple records have different values, do not treat
   one record's value as universal.
10. Distinguish dataset values from real-world quotations.

PDF POLICY EVIDENCE RULES:

1. Verify policy conditions using supplied PDF evidence.
2. Pay attention to waiting periods, exclusions,
   conditions and exceptions.
3. Do not confuse different waiting periods.
4. Do not assume a condition applies to every claim
   unless the evidence supports that interpretation.

SCORING:

0-3:
Mostly incorrect or contains important contradictions.

4-6:
Partially supported, ambiguous, or missing important details.

7-8:
Mostly supported with minor factual limitations.

9-10:
All important factual claims are fully supported
and correctly qualified by the evidence.

If evidence is insufficient, use "Insufficient Evidence".

Return ONLY valid JSON:

{{
    "score": 0,
    "verdict": "Incorrect",
    "explanation": "Explain the result.",
    "supported_claims": [],
    "unsupported_claims": [],
    "contradicted_claims": []
}}

Allowed verdicts:
"Correct",
"Partially Correct",
"Incorrect",
"Insufficient Evidence".
"""

    response = ask_groq(
        prompt,
        system_prompt=(
            "You are a careful factual accuracy evaluator. "
            "Evaluate every factual claim against the supplied "
            "evidence. Compare numerical values against the "
            "correct individual records. Never use outside "
            "knowledge. Return valid JSON only."
        )
    )

    try:

        # Extract the JSON object from the model response.
        start = response.find("{")
        end = response.rfind("}")

        if start == -1 or end == -1 or end < start:
            raise ValueError("No JSON object found.")

        result = json.loads(response[start:end + 1])

        score = result.get("score")

        if isinstance(score, bool) or not isinstance(
            score, (int, float)
        ):
            raise ValueError("Invalid accuracy score.")

        if not 0 <= score <= 10:
            raise ValueError("Score must be between 0 and 10.")

        allowed_verdicts = [
            "Correct",
            "Partially Correct",
            "Incorrect",
            "Insufficient Evidence"
        ]

        if result.get("verdict") not in allowed_verdicts:
            raise ValueError("Invalid accuracy verdict.")

        for field in [
            "supported_claims",
            "unsupported_claims",
            "contradicted_claims"
        ]:

            if not isinstance(result.get(field), list):
                raise ValueError(f"Invalid {field}.")

        if not isinstance(result.get("explanation"), str):
            raise ValueError("Invalid explanation.")

        # Deterministic CSV numerical validation.
        numerical_errors = validate_csv_numerical_claims(
            question,
            answer,
            evidence
        )

        if numerical_errors:

            result["score"] = min(result["score"], 2)
            result["verdict"] = "Incorrect"

            result["contradicted_claims"].extend(
                numerical_errors
            )

            result["explanation"] += (
                " Deterministic numerical validation also "
                "identified a mismatch between an answer value "
                "and its corresponding CSV evidence record."
            )

        return {
            "agent": "Accuracy Judge",
            "score": result["score"],
            "verdict": result["verdict"],
            "explanation": result["explanation"],
            "supported_claims": result["supported_claims"],
            "unsupported_claims": result["unsupported_claims"],
            "contradicted_claims": result["contradicted_claims"]
        }

    except (json.JSONDecodeError, ValueError) as error:

        raise RuntimeError(
            f"Accuracy evaluation failed: {error}. "
            f"Model response: {response}"
        )
