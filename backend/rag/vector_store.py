
from uuid import uuid4

import chromadb

from backend.rag.config import CHROMA_DIR, COLLECTION_NAME, TOP_K


client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


def delete_documents_by_source(source):
    if not source:
        return 0

    existing = collection.get(
        where={"source": str(source)},
        include=[]
    )

    ids = existing["ids"]

    if ids:
        collection.delete(ids=ids)

    return len(ids)


def add_documents(chunks, embeddings):
    if len(chunks) != len(embeddings):
        raise ValueError("Chunks and embeddings count must match.")

    if not chunks:
        return 0

    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        ids.append(str(uuid4()))
        documents.append(chunk["text"])

        metadatas.append({
            "source": str(chunk["source"]),
            "page": int(chunk["page"]),
            "chunk_index": int(chunk["chunk_index"])
        })

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(chunks)


def search_documents(query_embedding, top_k=TOP_K):
    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    evidence = []

    if not result["documents"] or not result["documents"][0]:
        return evidence

    for i in range(len(result["documents"][0])):

        metadata = result["metadatas"][0][i]

        evidence.append({
            "text": result["documents"][0][i],
            "source": metadata["source"],
            "page": metadata["page"],
            "chunk_index": metadata["chunk_index"],
            "distance": result["distances"][0][i]
        })

    return evidence
