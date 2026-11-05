
import pytest

from backend.rag import retriever


def test_retrieve_evidence(monkeypatch):
    def mock_generate_query_embedding(query):
        return [0.1, 0.2, 0.3]

    def mock_search_documents(query_embedding, top_k=3):
        return [
            {
                "text": "Applicants must be at least 21 years old.",
                "source": "sample_banking.txt",
                "page": 1,
                "chunk_index": 0,
                "distance": 0.1
            }
        ]

    monkeypatch.setattr(
        retriever,
        "generate_query_embedding",
        mock_generate_query_embedding
    )

    monkeypatch.setattr(
        retriever,
        "search_documents",
        mock_search_documents
    )

    results = retriever.retrieve_evidence(
        "What is the minimum applicant age?",
        top_k=3
    )

    assert len(results) == 1
    assert "21 years old" in results[0]["text"]
    assert results[0]["source"] == "sample_banking.txt"


def test_retrieve_empty_query():
    with pytest.raises(ValueError):
        retriever.retrieve_evidence("")


def test_retrieve_whitespace_query():
    with pytest.raises(ValueError):
        retriever.retrieve_evidence("   ")
