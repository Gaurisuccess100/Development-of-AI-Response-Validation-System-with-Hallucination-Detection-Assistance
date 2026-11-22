from backend.rag.config import CHROMA_DIR, COLLECTION_NAME
import chromadb

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = client.get_collection(name=COLLECTION_NAME)

print("\nTotal stored chunks:", collection.count())

result = collection.get(
    where={"page": 11},
    include=["documents", "metadatas"]
)

print("\nChunks found on PDF page 11:", len(result["ids"]))

chunks = []

for document, metadata in zip(result["documents"], result["metadatas"]):
    chunks.append((metadata["chunk_index"], document))

for index, text in sorted(chunks, key=lambda item: item[0]):
    print("\n" + "=" * 70)
    print("CHUNK INDEX:", index)
    print("=" * 70)
    print(text)
