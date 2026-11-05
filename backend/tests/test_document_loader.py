
import pytest
from backend.rag.document_loader import load_document


def test_load_txt_document(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "Banking loan eligibility policy.",
        encoding="utf-8"
    )

    document = load_document(file_path)

    assert document["source"] == "sample.txt"
    assert "Banking loan eligibility policy." in document["text"]
    assert len(document["pages"]) == 1


def test_load_missing_document(tmp_path):
    file_path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        load_document(file_path)


def test_unsupported_file_format(tmp_path):
    file_path = tmp_path / "sample.docx"
    file_path.write_text("Sample", encoding="utf-8")

    with pytest.raises(ValueError):
        load_document(file_path)


def test_empty_txt_document(tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")

    document = load_document(file_path)

    assert document["text"] == ""
    assert document["pages"] == []
