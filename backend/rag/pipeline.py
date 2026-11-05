from uuid import uuid4

from backend.rag.document_loader import load_document

from backend.rag.chunker import chunk_document

from backend.rag.embeddings import generate_embeddings

from backend.rag.vector_store import add_documents

from backend.rag.retriever import retrieve_evidence


def ingest_document(file_path):

    # Step 1: Load document
    document = load_document(file_path)

    if not document["text"].strip():

        return {
            "document_id": None,
            "chunks_added": 0,
            "source": document["source"],
            "message": "No readable text found."
        }

    # Step 2: Generate document ID
    document_id = str(uuid4())

    # Step 3: Create chunks
    chunks = chunk_document(document)

    # Step 4: Generate embeddings
    texts = [chunk["text"] for chunk in chunks]

    embeddings = generate_embeddings(texts)

    # Step 5: Store in ChromaDB
    chunks_added = add_documents(
        chunks,
        embeddings
    )

    return {
        "document_id": document_id,
        "chunks_added": chunks_added,
        "source": document["source"],
        "message": "Document successfully indexed."
    }


def answer_with_evidence(question, top_k=3):

    evidence = retrieve_evidence(
        question,
        top_k=top_k
    )

    return {
        "question": question,
        "evidence": evidence,
        "evidence_count": len(evidence)
    }