
from uuid import uuid4

from backend.rag.vector_store import add_documents, search_documents


def test_add_and_search_documents():
    unique_source = f"test_{uuid4().hex}.txt"

    chunks = [
        {
            "text": "Applicants must be at least 21 years old.",
            "source": unique_source,
            "page": 1,
            "chunk_index": 0
        }
    ]

    # 384-dimensional vector, matching MiniLM embeddings
    embedding = [0.0] * 384
    embedding[0] = 1.0

    embeddings = [embedding]

    added_count = add_documents(chunks, embeddings)

    assert added_count == 1

    results = search_documents(
        query_embedding=embedding,
        top_k=10
    )

    matching_results = [
        result for result in results
        if result["source"] == unique_source
    ]

    assert len(matching_results) >= 1
    assert "21 years old" in matching_results[0]["text"]
    assert matching_results[0]["page"] == 1


def test_add_empty_documents():
    result = add_documents([], [])

    assert result == 0


def test_mismatched_chunks_and_embeddings():
    chunks = [
        {
            "text": "Sample text",
            "source": "sample.txt",
            "page": 1,
            "chunk_index": 0
        }
    ]

    embeddings = []

    try:
        add_documents(chunks, embeddings)
    except ValueError:
        assert True
    else:
        assert False, "Expected ValueError for mismatched inputs"
