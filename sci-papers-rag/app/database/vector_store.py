from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict

class VectorStoreManager:
    def __init__(self, persist_directory: str = "./data/chroma"):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None

    def initialize_store(self):
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )

    def add_documents(self, texts: List[str], metadatas: List[Dict] = None):
        if self.vector_store is None:
            self.initialize_store()
        
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)

    def search_similar(self, query: str, k: int = 5):
        if self.vector_store is None:
            self.initialize_store()
            
        return self.vector_store.similarity_search(query, k=k) 