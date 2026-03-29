from __future__ import annotations

import logging
import os
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".doc": Docx2txtLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
}


def load_document(file_path: str) -> list[Document]:
    ext = Path(file_path).suffix.lower()
    loader_cls = LOADER_MAP.get(ext)
    if not loader_cls:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {list(LOADER_MAP.keys())}")

    loader = loader_cls(file_path)
    docs = loader.load()

    for doc in docs:
        doc.metadata["source"] = os.path.basename(file_path)
        doc.metadata["file_type"] = ext

    return docs


def chunk_documents(documents: list[Document]) -> list[Document]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def process_and_embed(file_path: str, namespace: str) -> int:
    """Full pipeline: load file -> chunk -> embed -> upsert to Pinecone.

    Returns the number of chunks stored.
    """
    from app.rag.embeddings import get_retriever

    documents = load_document(file_path)
    chunks = chunk_documents(documents)

    if not chunks:
        logger.warning(f"No content extracted from {file_path}")
        return 0

    retriever = get_retriever()
    count = retriever.upsert(chunks, namespace=namespace)
    logger.info(f"Stored {count} chunks from {file_path} in namespace {namespace}")
    return count
