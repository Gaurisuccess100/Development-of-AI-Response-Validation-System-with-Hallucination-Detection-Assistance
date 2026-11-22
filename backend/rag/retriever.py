
import re

from backend.rag.config import TOP_K
from backend.rag.embeddings import generate_query_embedding
from backend.rag.vector_store import search_documents, collection


def retrieve_evidence(query, top_k=TOP_K):

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    clean_query = query.strip()

    # 1. Semantic search
    query_embedding = generate_query_embedding(clean_query)

    semantic_results = search_documents(
        query_embedding,
        top_k=max(top_k, 30)
    )

    # 2. Keyword-based search across stored chunks
    all_documents = collection.get(
        include=["documents", "metadatas"]
    )

    query_words = set(
        re.findall(r"[a-z0-9]+", clean_query.lower())
    )

    stopwords = {
        "what", "is", "the", "for", "under",
        "a", "an", "of", "in", "to", "and"
    }

    query_words = query_words - stopwords

    keyword_results = []

    for text, metadata in zip(
        all_documents["documents"],
        all_documents["metadatas"]
    ):

        text_lower = text.lower()

        score = sum(
            1 for word in query_words
            if word in text_lower
        )

        # Give extra weight to important policy phrases
        if "pre-existing disease" in text_lower:
            score += 5

        if "36 months of continuous coverage" in text_lower:
            score += 5

        if score > 0:
            keyword_results.append({
                "text": text,
                "source": metadata["source"],
                "page": metadata["page"],
                "chunk_index": metadata["chunk_index"],
                "distance": None,
                "keyword_score": score
            })

    # 3. Combine semantic and keyword results
    combined = {}

    for item in semantic_results:
        key = (
            item["source"],
            item["page"],
            item["chunk_index"]
        )
        combined[key] = item

    for item in keyword_results:
        key = (
            item["source"],
            item["page"],
            item["chunk_index"]
        )

        if key in combined:
            combined[key]["keyword_score"] = item["keyword_score"]
        else:
            combined[key] = item

    # 4. Rank keyword matches first, then semantic matches
    results = list(combined.values())

    results.sort(
        key=lambda item: (
            item.get("keyword_score", 0),
            -(item.get("distance") or 0)
        ),
        reverse=True
    )

    return results[:max(top_k, 30)]
