from pathlib import Path
import pymupdf


def load_document(file_path):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    extension = path.suffix.lower()
    pages = []

    if extension == ".txt":
        text = path.read_text(encoding="utf-8")

        if text.strip():
            pages.append({
                "page": 1,
                "text": text
            })

    elif extension == ".pdf":
        with pymupdf.open(path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()

                if text:
                    pages.append({
                        "page": page_number,
                        "text": text
                    })

    else:
        raise ValueError("Only PDF and TXT files are supported.")

    full_text = "\n".join(item["text"] for item in pages)

    return {
        "source": path.name,
        "text": full_text,
        "pages": pages
    }
