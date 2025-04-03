import os
import chromadb
import requests

from typing import TypedDict
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END

from dotenv import load_dotenv
from src.ingestion.document_loader import DocumentLoader

load_dotenv('../.env')

# Set up vector store (ChromaDB)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings())

# LLM for summarization
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)

# Initialize document loader
doc_loader = DocumentLoader(embeddings=OpenAIEmbeddings())

# Update fetch_papers function
def fetch_papers(topic):
    return doc_loader.fetch_arxiv_papers(topic)

# You can also add a function to load local PDFs when needed
def load_local_papers(directory):
    documents = doc_loader.load_local_pdfs(directory)
    store_papers(documents)

# Store papers in ChromaDB
def store_papers(papers):
    for paper in papers:
        vectorstore.add_texts(texts=[paper['abstract']], metadatas=[{"title": paper['title'], "url": paper['url']}])

# Retrieve relevant papers
def retrieve_papers(query):
    return vectorstore.similarity_search(query, k=3)

# Summarization workflow
def summarize_papers(papers):
    prompt = PromptTemplate(template="Summarize these papers: {papers}", input_variables=["papers"])
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run({"papers": papers})

# Define LangGraph workflow
class ResearchState(TypedDict):
    """
    State for the research workflow.
    """
    query: str
    papers: list
    summary: str

workflow = StateGraph(ResearchState)

workflow.add_node("fetch", fetch_papers)
workflow.add_node("store", store_papers)
workflow.add_node("retrieve", retrieve_papers)
workflow.add_node("summarize", summarize_papers)
workflow.add_edge("fetch", "store")
workflow.add_edge("store", "retrieve")
workflow.add_edge("retrieve", "summarize")
workflow.set_entry_point("fetch")
workflow.set_finish_point("summarize")

app = workflow.compile()

app.get_graph().draw_mermaid_png(output_file_path="graph.png")


def run_agent(query):
    return app.invoke(input={'query': query})

if __name__ == "__main__":
    query = "computer vision"
    result = run_agent(query)
    print("Final Summary:\n", result.summary)
    print("Papers:\n", result.papers)