from backend.rag.embeddings import generate_query_embedding

from backend.rag.vector_store import search_documents


def retrieve_evidence(query, top_k=3):

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    query_embedding = generate_query_embedding(
        query.strip()
    )

    evidence = search_documents(
        query_embedding,
        top_k=top_k
    )

    return evidence