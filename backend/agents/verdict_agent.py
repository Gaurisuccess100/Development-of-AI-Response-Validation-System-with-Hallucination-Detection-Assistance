
import json
import re

from backend.agents.llm_client import ask_groq


def generate_final_verdict(
    question,
    answer,
    relevance_result,
    accuracy_result,
    hallucination_result,
    completeness_result
):

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not answer or not answer.strip():
        raise ValueError("Answer cannot be empty.")

    results = {
        "relevance": relevance_result,
        "accuracy": accuracy_result,
        "hallucination": hallucination_result,
        "completeness": completeness_result
    }

    # Validate agent results.
    for agent_name, agent_result in results.items():
        if not isinstance(agent_result, dict):
            raise ValueError(
                f"Invalid result received from {agent_name} agent."
            )

    # Do not make a definitive decision without evidence.
    if (
        accuracy_result.get("verdict") == "Insufficient Evidence"
        or accuracy_result.get("score") is None
        or hallucination_result.get("verdict") == "Insufficient Evidence"
        or hallucination_result.get("hallucination_detected") is None
    ):
        return {
            "agent": "Verdict Agent",
            "overall_score": None,
            "final_verdict": "Insufficient Evidence",
            "reason": (
                "There is insufficient evidence to reliably "
                "verify the AI-generated answer."
            ),
            "strengths": [],
            "issues": [
                "A reliable factual evaluation could not be completed."
            ]
        }

    evaluation_data = json.dumps(results, indent=2)

    prompt = f"""
You are the Final Verdict Agent in an AI Response
Validation System.

Your responsibility is to combine the results of four agents
and produce a fair final evaluation.

USER QUESTION:
{question}

AI-GENERATED ANSWER:
{answer}

INDIVIDUAL AGENT RESULTS:
{evaluation_data}

EVALUATION RULES:

1. Consider all four agents:
   - Relevance Judge
   - Accuracy Judge
   - Hallucination Detection Agent
   - Completeness Judge

2. Accuracy and hallucination detection are especially
   important for factual reliability.

3. A detected factual hallucination should normally
   result in Fail.

4. An accuracy verdict of Incorrect should normally
   result in Fail.

5. Partially Correct answers should not receive Pass
   unless the accuracy agent's result is corrected
   by stronger evidence in the provided results.

6. If important information or context is missing,
   consider the completeness score and missing_information.

7. If the answer is relevant but has accuracy or
   completeness limitations, use Needs Improvement.

8. Do not treat a claim as hallucinated merely because
   it is incomplete or ambiguous.

9. Do not penalize an answer for irrelevant details
   that were not requested.

10. Do not invent facts or agent findings.

11. Consider PDF and CSV evidence findings through
    the results of the individual agents.

SCORING GUIDELINES:

9-10:
Excellent answer. Relevant, factually supported,
complete and free from detected hallucinations.

8:
Good answer with only minor limitations.
May receive Pass if factual reliability is strong.

5-7:
Needs Improvement. Some important context,
accuracy or completeness limitations exist.

0-4:
Fail. Serious factual errors or major reliability problems.

FINAL VERDICT GUIDELINES:

Pass:
The answer is relevant, sufficiently accurate,
complete and has no detected hallucinations.

Needs Improvement:
The answer has some limitations but is not
seriously factually incorrect.

Fail:
The answer contains a detected factual hallucination,
serious contradiction or clearly incorrect information.

Insufficient Evidence:
There is not enough evidence to make a reliable decision.

Return ONLY valid JSON:

{{
    "overall_score": 0,
    "final_verdict": "Needs Improvement",
    "reason": "Explain the final evaluation.",
    "strengths": [],
    "issues": []
}}

Rules:
- overall_score must be between 0 and 10.
- final_verdict must be one of:
  "Pass", "Needs Improvement", "Fail",
  "Insufficient Evidence".
- Give a clear reason based on agent results.
- Do not invent evaluation results.
- Do not ignore a serious accuracy or hallucination issue.
"""

    response = ask_groq(
        prompt,
        system_prompt=(
            "You are a strict and fair final AI response evaluator. "
            "Combine all four agent results carefully. "
            "Prioritize factual reliability and evidence-based reasoning. "
            "Return valid JSON only."
        )
    )

    try:

        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:
            raise ValueError("No JSON object found.")

        result = json.loads(match.group())

        score = result.get("overall_score")

        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not 0 <= score <= 10
        ):
            raise ValueError("Invalid overall score.")

        allowed_verdicts = [
            "Pass",
            "Needs Improvement",
            "Fail",
            "Insufficient Evidence"
        ]

        if result.get("final_verdict") not in allowed_verdicts:
            raise ValueError("Invalid final verdict.")

        if not isinstance(result.get("reason"), str):
            raise ValueError("Invalid reason.")

        if not isinstance(result.get("strengths"), list):
            raise ValueError("Invalid strengths.")

        if not isinstance(result.get("issues"), list):
            raise ValueError("Invalid issues.")

        # Apply safety rules to prevent an overly positive verdict.
        accuracy_verdict = accuracy_result.get("verdict", "")
        hallucination_detected = hallucination_result.get(
            "hallucination_detected"
        )
        completeness_score = completeness_result.get("score")

        # A factual hallucination or clearly incorrect answer
        # must not receive Pass.
        if (
            hallucination_detected is True
            or accuracy_verdict == "Incorrect"
        ):
            result["final_verdict"] = "Fail"
            result["overall_score"] = min(score, 4)

        else:

            # Partially correct or significantly incomplete answers
            # cannot receive Pass.
            if (
                accuracy_verdict == "Partially Correct"
                or (
                    isinstance(completeness_score, (int, float))
                    and completeness_score <= 6
                )
            ):
                if result["final_verdict"] == "Pass":
                    result["final_verdict"] = "Needs Improvement"

                if result["overall_score"] >= 8:
                    result["overall_score"] = 7

            # Keep score and verdict reasonably consistent.
            if result["overall_score"] <= 4:
                result["final_verdict"] = "Fail"

            elif result["overall_score"] <= 7:
                if result["final_verdict"] == "Pass":
                    result["final_verdict"] = "Needs Improvement"

            elif result["overall_score"] >= 8:
                if result["final_verdict"] == "Fail":
                    result["overall_score"] = 4

        return {
            "agent": "Verdict Agent",
            "overall_score": result["overall_score"],
            "final_verdict": result["final_verdict"],
            "reason": result["reason"],
            "strengths": result["strengths"],
            "issues": result["issues"]
        }

    except (json.JSONDecodeError, ValueError) as error:

        raise RuntimeError(
            f"Final verdict generation failed: {error}. "
            f"Model response: {response}"
        )
