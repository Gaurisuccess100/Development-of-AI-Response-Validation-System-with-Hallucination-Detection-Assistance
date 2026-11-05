from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"

CHROMA_DIR = PROJECT_ROOT / "backend" / "chroma_db"

COLLECTION_NAME = "evalora_knowledge"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 500

CHUNK_OVERLAP = 100

TOP_K = 3

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)