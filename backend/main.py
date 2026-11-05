from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.rag.pipeline import ingest_document, answer_with_evidence


app = FastAPI(
    title="AI Response Quality Evaluator",
    description="Backend API for AI response evaluation and RAG evidence retrieval",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluationRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000)
    answer: str = Field(..., min_length=1, max_length=30000)
    reference_answer: str | None = None


class IngestRequest(BaseModel):
    file_path: str


@app.get("/")
def home():
    return {"message": "AI Response Quality Evaluator API is running"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}


@app.post("/api/ingest")
def ingest(request: IngestRequest):
    try:
        return ingest_document(request.file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/evaluate")
def evaluate(request: EvaluationRequest):
    try:
        evidence = answer_with_evidence(request.question)

        return {
            "question": request.question,
            "answer": request.answer,
            "reference_answer": request.reference_answer,
            "evidence": evidence
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))