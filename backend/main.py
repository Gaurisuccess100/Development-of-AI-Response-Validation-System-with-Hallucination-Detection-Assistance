
import json
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# RAG and dataset imports
from backend.rag.pipeline import ingest_document
from backend.dataset_query import search_policies, compare_companies
from backend.evidence.evidence_retriever import retrieve_combined_evidence

# All five AI agents
from backend.agents.relevance_agent import evaluate_relevance
from backend.agents.accuracy_agent import evaluate_accuracy
from backend.agents.hallucination_agent import detect_hallucinations
from backend.agents.completeness_agent import evaluate_completeness
from backend.agents.verdict_agent import generate_final_verdict


app = FastAPI(
    title="AI Response Validator",
    description=(
        "Development of AI Response Validation System "
        "with Hallucination Detection Assistance"
    ),
    version="1.0.0"
)


# CORS configuration
# CORS configuration
frontend_url = os.getenv("FRONTEND_URL", "").strip()

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class EvaluationRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000)
    answer: str = Field(..., min_length=1, max_length=30000)
    reference_answer: str | None = None


class IngestRequest(BaseModel):
    file_path: str


# Convert PDF and CSV evidence into a common format
def prepare_agent_evidence(pdf_evidence, csv_evidence):

    prepared = []

    # PDF evidence
    for item in pdf_evidence:

        if isinstance(item, dict):
            text = item.get("text", "")

            if text:
                prepared.append({
                    "text": str(text),
                    "source": item.get("source", "Policy PDF"),
                    "page": item.get("page", "Unknown")
                })

        elif isinstance(item, str) and item.strip():
            prepared.append({
                "text": item,
                "source": "Policy PDF",
                "page": "Unknown"
            })

    # CSV evidence
    for index, item in enumerate(csv_evidence):

        if isinstance(item, dict):
            csv_text = json.dumps(item, indent=2, default=str)
        else:
            csv_text = str(item)

        if csv_text.strip():
            prepared.append({
                "text": (
                    "Insurance dataset record:\n" + csv_text
                ),
                "source": "Insurance CSV Dataset",
                "page": "N/A"
            })

    return prepared




def select_agent_evidence(pdf_evidence, csv_evidence):

    # When both PDF and CSV evidence are available
    if pdf_evidence and csv_evidence:
        return pdf_evidence[:3] + csv_evidence[:10]

    # CSV-only evaluation
    if csv_evidence:
        return csv_evidence[:10]

    # PDF-only evaluation
    return pdf_evidence[:5]


# API endpoints
@app.get("/")
def root():
    return {
        "message": "AI Response Validator API is running"
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy"
    }


# Upload and index a policy document
@app.post("/api/ingest")
def ingest(request: IngestRequest):

    try:
        return ingest_document(request.file_path)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# Main AI response evaluation endpoint
@app.post("/api/evaluate")
def evaluate(request: EvaluationRequest):

    try:
        # STEP 1: Retrieve PDF and CSV evidence
        retrieved = retrieve_combined_evidence(
            request.question
        )

        pdf_evidence = retrieved.get("pdf_evidence", [])
        csv_evidence = retrieved.get("csv_evidence", [])

        # STEP 2: Convert evidence into a common format
        all_agent_evidence = prepare_agent_evidence(
            pdf_evidence,
            csv_evidence
        )

        # STEP 3: Limit evidence to avoid Groq token limits
        agent_evidence = select_agent_evidence(
            [
                item for item in all_agent_evidence
                if item["source"] != "Insurance CSV Dataset"
            ],
            [
                item for item in all_agent_evidence
                if item["source"] == "Insurance CSV Dataset"
            ]
        )

        # STEP 4: Relevance evaluation
        relevance_result = evaluate_relevance(
            request.question,
            request.answer
        )

        # STEP 5: Evaluate accuracy, hallucination and completeness
        if agent_evidence:

            accuracy_result = evaluate_accuracy(
                request.question,
                request.answer,
                agent_evidence
            )

            hallucination_result = detect_hallucinations(
                request.question,
                request.answer,
                agent_evidence
            )

            completeness_result = evaluate_completeness(
                request.question,
                request.answer,
                agent_evidence
            )

        else:
            # Do not claim factual verification without evidence.
            accuracy_result = {
                "agent": "Accuracy Judge",
                "score": None,
                "verdict": "Insufficient Evidence",
                "explanation": (
                    "No usable reference evidence was retrieved."
                ),
                "supported_claims": [],
                "unsupported_claims": [],
                "contradicted_claims": []
            }

            hallucination_result = {
                "agent": "Hallucination Detection Agent",
                "hallucination_detected": None,
                "verdict": "Insufficient Evidence",
                "supported_claims": [],
                "hallucinated_claims": [],
                "explanation": (
                    "No evidence was available to verify hallucinations."
                )
            }

            completeness_result = {
                "agent": "Completeness Judge",
                "score": None,
                "verdict": "Insufficient Evidence",
                "missing_information": [],
                "explanation": (
                    "No reference evidence was available "
                    "to evaluate completeness."
                )
            }

        # STEP 6: Generate final verdict using all four results
        final_result = generate_final_verdict(
            question=request.question,
            answer=request.answer,
            relevance_result=relevance_result,
            accuracy_result=accuracy_result,
            hallucination_result=hallucination_result,
            completeness_result=completeness_result
        )

        # STEP 7: Return complete evaluation
        return {
            "question": request.question,
            "answer": request.answer,
            "reference_answer": request.reference_answer,

            "evaluation_status": "completed",

            "evidence": retrieved,

            "agent_evidence_count": len(agent_evidence),

            "agents": {
                "relevance": relevance_result,
                "accuracy": accuracy_result,
                "hallucination": hallucination_result,
                "completeness": completeness_result,
                "verdict": final_result
            },

            "agents_status": "completed",

            "final_verdict": final_result
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Search insurance dataset
@app.get("/api/dataset/search")
def dataset_search(
    company: str | None = None,
    min_coverage: float | None = Query(default=None, ge=0),
    max_premium: float | None = Query(default=None, ge=0),
    cashless: str | None = None
):

    try:
        results = search_policies(
            company=company,
            min_coverage=min_coverage,
            max_premium=max_premium,
            cashless=cashless
        )

        return {
            "total_results": len(results),
            "filters": {
                "company": company,
                "min_coverage": min_coverage,
                "max_premium": max_premium,
                "cashless": cashless
            },
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Compare insurance companies
@app.get("/api/dataset/compare")
def dataset_compare():

    try:
        results = compare_companies()

        return {
            "total_companies": len(results),
            "comparison": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
