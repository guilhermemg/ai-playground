import os

import sys
if '../..' not in sys.path:
    sys.path.insert(0, '../..')


from dotenv import load_dotenv

load_dotenv()

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFMinerLoader
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from src.consts import INDEX_NAME


embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


def ingest_docs():
    base_path = "../data/papers"

    print("****Loading to vectorstore started ***")
    n = len(os.listdir(base_path))
    print(f"Going to load {n} documents to Pinecone")

    for f in os.listdir(base_path):
        print("Loading document", f)
        loader = PDFMinerLoader(os.path.join(base_path, f))

        raw_documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=50)
        documents = text_splitter.split_documents(raw_documents)
        
        for doc in documents:
            new_url = doc.metadata["source"]
            doc.metadata.update({"source": new_url})

    print(f"Going to add {len(documents)} to Pinecone")
    PineconeVectorStore.from_documents(documents, embeddings, index_name=INDEX_NAME)
    print("****Loading to vectorstore done ***")



if __name__ == "__main__":
    ingest_docs()