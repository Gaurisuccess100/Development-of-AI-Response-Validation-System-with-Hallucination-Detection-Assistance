from uuid import uuid4

import chromadb

from backend.rag.config import CHROMA_DIR, COLLECTION_NAME


client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


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


def search_documents(query_embedding, top_k=3):

    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    evidence = []

    for i in range(len(result["documents"][0])):

        evidence.append({
            "text": result["documents"][0][i],
            "source": result["metadatas"][0][i]["source"],
            "page": result["metadatas"][0][i]["page"],
            "chunk_index": result["metadatas"][0][i]["chunk_index"],
            "distance": result["distances"][0][i]
        })

    return evidence