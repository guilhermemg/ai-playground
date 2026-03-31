from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class PineconeRetriever:
    def __init__(self):
        settings = get_settings()
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            dimensions=settings.pinecone_dimension,
            api_key=settings.openai_api_key,
        )
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self.pc.Index(settings.pinecone_index_name)
        self.top_k = settings.retrieval_top_k

    def upsert(self, documents: list[Document], namespace: str) -> int:
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        embeddings = self.embeddings.embed_documents(texts)

        vectors = []
        for i, (emb, text, meta) in enumerate(zip(embeddings, texts, metadatas)):
            vectors.append({
                "id": f"{namespace}_{i}",
                "values": emb,
                "metadata": {**meta, "text": text},
            })

        batch_size = 100
        total = 0
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self.index.upsert(vectors=batch, namespace=namespace)
            total += len(batch)

        return total

    def retrieve(self, query: str, namespace: str) -> list[Document]:
        query_embedding = self.embeddings.embed_query(query)
        results = self.index.query(
            vector=query_embedding,
            namespace=namespace,
            top_k=self.top_k,
            include_metadata=True,
        )

        docs = []
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            text = meta.pop("text", "")
            docs.append(Document(page_content=text, metadata=meta))

        return docs

    def delete_namespace(self, namespace: str):
        try:
            self.index.delete(delete_all=True, namespace=namespace)
        except Exception as e:
            logger.warning(f"Failed to delete namespace {namespace}: {e}")


_retriever: PineconeRetriever | None = None


def get_retriever() -> PineconeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = PineconeRetriever()
    return _retriever
