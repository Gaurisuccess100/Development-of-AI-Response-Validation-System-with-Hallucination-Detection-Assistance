
from sentence_transformers import SentenceTransformer

from backend.rag.config import EMBEDDING_MODEL


_model = None


def get_model():
    global _model

    if _model is None:
        print("Loading embedding model...")
        _model = SentenceTransformer(EMBEDDING_MODEL)

    return _model


def generate_embeddings(texts):

    if not texts:
        return []

    model = get_model()

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings.tolist()


def generate_query_embedding(query):

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    model = get_model()

    embedding = model.encode(
        query.strip(),
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embedding.tolist()
