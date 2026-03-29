import pytest
from unittest.mock import patch, MagicMock

from langchain_core.documents import Document


@patch("app.rag.embeddings.get_settings")
@patch("app.rag.embeddings.Pinecone")
@patch("app.rag.embeddings.OpenAIEmbeddings")
def test_retriever_upsert(mock_embeddings_cls, mock_pinecone_cls, mock_settings):
    mock_settings.return_value = MagicMock(
        openai_api_key="test",
        openai_embedding_model="text-embedding-3-small",
        pinecone_api_key="test",
        pinecone_index_name="test-index",
        retrieval_top_k=5,
    )

    mock_embeddings = MagicMock()
    mock_embeddings.embed_documents.return_value = [[0.1] * 1536, [0.2] * 1536]
    mock_embeddings_cls.return_value = mock_embeddings

    mock_index = MagicMock()
    mock_pc = MagicMock()
    mock_pc.Index.return_value = mock_index
    mock_pinecone_cls.return_value = mock_pc

    from app.rag.embeddings import PineconeRetriever

    retriever = PineconeRetriever()
    docs = [
        Document(page_content="Test content 1", metadata={"source": "test.txt"}),
        Document(page_content="Test content 2", metadata={"source": "test.txt"}),
    ]

    count = retriever.upsert(docs, namespace="test_ns")
    assert count == 2
    mock_index.upsert.assert_called_once()


@patch("app.rag.embeddings.get_settings")
@patch("app.rag.embeddings.Pinecone")
@patch("app.rag.embeddings.OpenAIEmbeddings")
def test_retriever_retrieve(mock_embeddings_cls, mock_pinecone_cls, mock_settings):
    mock_settings.return_value = MagicMock(
        openai_api_key="test",
        openai_embedding_model="text-embedding-3-small",
        pinecone_api_key="test",
        pinecone_index_name="test-index",
        retrieval_top_k=5,
    )

    mock_embeddings = MagicMock()
    mock_embeddings.embed_query.return_value = [0.1] * 1536
    mock_embeddings_cls.return_value = mock_embeddings

    mock_index = MagicMock()
    mock_index.query.return_value = {
        "matches": [
            {"metadata": {"text": "Relevant content", "source": "doc.pdf"}, "score": 0.95},
        ]
    }
    mock_pc = MagicMock()
    mock_pc.Index.return_value = mock_index
    mock_pinecone_cls.return_value = mock_pc

    from app.rag.embeddings import PineconeRetriever

    retriever = PineconeRetriever()
    results = retriever.retrieve("test query", namespace="test_ns")

    assert len(results) == 1
    assert results[0].page_content == "Relevant content"
