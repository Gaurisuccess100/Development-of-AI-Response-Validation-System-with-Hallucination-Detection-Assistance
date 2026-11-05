from backend.rag.config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_document(
    document,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP
):

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks = []

    step = chunk_size - overlap

    for page_data in document["pages"]:

        text = page_data["text"]

        start = 0
        chunk_index = 0

        while start < len(text):

            end = start + chunk_size

            chunk_text = text[start:end].strip()

            if chunk_text:

                chunks.append({
                    "text": chunk_text,
                    "source": document["source"],
                    "page": page_data["page"],
                    "chunk_index": chunk_index
                })

            start += step
            chunk_index += 1

    return chunks