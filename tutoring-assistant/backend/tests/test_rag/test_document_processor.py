import os
import tempfile
import pytest

from app.rag.document_processor import load_document, chunk_documents


def test_load_text_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("This is a test document about physics.\n" * 50)
        f.flush()
        path = f.name

    try:
        docs = load_document(path)
        assert len(docs) >= 1
        assert "physics" in docs[0].page_content
        assert docs[0].metadata["file_type"] == ".txt"
    finally:
        os.unlink(path)


def test_load_unsupported_file():
    with pytest.raises(ValueError, match="Unsupported file type"):
        load_document("test.xyz")


def test_chunk_documents():
    from langchain_core.documents import Document

    long_text = "This is a test sentence. " * 200
    docs = [Document(page_content=long_text, metadata={"source": "test.txt"})]

    chunks = chunk_documents(docs)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.page_content) <= 1200  # chunk_size + overlap buffer
