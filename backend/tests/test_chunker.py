
from backend.rag.chunker import chunk_document


def test_chunk_document_returns_chunks():
    document = {
        "source": "sample.txt",
        "pages": [
            {
                "page": 1,
                "text": "This is a sample banking document. " * 20
            }
        ]
    }

    chunks = chunk_document(
        document,
        chunk_size=100,
        overlap=20
    )

    assert len(chunks) > 0
    assert chunks[0]["source"] == "sample.txt"
    assert chunks[0]["page"] == 1
    assert "text" in chunks[0]
    assert "chunk_index" in chunks[0]


def test_chunk_document_empty_pages():
    document = {
        "source": "empty.txt",
        "pages": []
    }

    chunks = chunk_document(document)

    assert chunks == []
