
import hashlib
import re
import math

# Lightweight feature-hashing embeddings.
# No PyTorch or SentenceTransformer required.

DIMENSIONS = 384


def _embed_text(text):
    vector = [0.0] * DIMENSIONS

    words = re.findall(r"[a-zA-Z0-9]+", text.lower())

    if not words:
        return vector

    # Include individual words and adjacent word pairs.
    features = words + [
        f"{words[i]}_{words[i + 1]}"
        for i in range(len(words) - 1)
    ]

    for feature in features:
        digest = hashlib.blake2b(
            feature.encode("utf-8"),
            digest_size=8
        ).digest()

        index = int.from_bytes(digest[:4], "big") % DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0

        vector[index] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))

    if magnitude:
        vector = [value / magnitude for value in vector]

    return vector


def generate_embeddings(texts):
    if not texts:
        return []

    return [_embed_text(text) for text in texts]


def generate_query_embedding(query):
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    return _embed_text(query.strip())
