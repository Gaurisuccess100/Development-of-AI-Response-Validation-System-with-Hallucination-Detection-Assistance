
from backend.rag.document_loader import load_document
from backend.rag.chunker import chunk_document

document = load_document("backend/uploads/hdfc_policy.pdf")
chunks = chunk_document(document)

page_chunks = [
    chunk for chunk in chunks
    if chunk["page"] == 11
]

print(f"Total chunks on page 11: {len(page_chunks)}")

for chunk in page_chunks:
    print("\n" + "=" * 70)
    print("CHUNK INDEX:", chunk["chunk_index"])
    print("=" * 70)
    print(chunk["text"])
