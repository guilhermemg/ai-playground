import os
import requests
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFMinerLoader
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

class DocumentLoader:
    def __init__(self, embeddings=None):
        self.embeddings = embeddings or OpenAIEmbeddings(model="text-embedding-3-small")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600, 
            chunk_overlap=50
        )

    def load_local_pdfs(self, base_path: str) -> List[Document]:
        """Load and process local PDF documents"""
        documents = []
        for f in os.listdir(base_path):
            print(f"Loading document {f}")
            loader = PDFMinerLoader(os.path.join(base_path, f))
            raw_documents = loader.load()
            split_docs = self.text_splitter.split_documents(raw_documents)
            documents.extend(split_docs)
        return documents

    def fetch_arxiv_papers(self, topic: str) -> List[Dict]:
        """Fetch papers from arXiv API"""
        url = f"http://export.arxiv.org/api/query?search_query={topic}&max_results=5"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Error fetching papers: {response.status_code}")
        # TODO: Parse XML response and return structured data
        return []  # Replace with actual parsed data 