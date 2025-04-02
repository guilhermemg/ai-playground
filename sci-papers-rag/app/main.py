from typing import List, Dict
import arxiv
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_extraction_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class ArxivPaperSummarizer:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0)
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)

    def search_papers(self, topic: str, max_results: int = 5) -> List[arxiv.Result]:
        client = arxiv.Client()
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
        )
        return list(client.results(search))

    def process_paper(self, paper: arxiv.Result) -> Dict:
        # Create a safe filename from the paper ID only
        paper_id = paper.get_short_id().replace('/', '_')
        pdf_path = os.path.join(self.data_dir, f"{paper_id}.pdf")
        
        # Download and read the paper
        try:
            # Download PDF using our own PDF processor
            from utils.pdf_processor import PDFProcessor
            pdf_content = PDFProcessor.download_pdf(paper.pdf_url)
            
            # Save the PDF
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)
                
        except Exception as e:
            print(f"Error downloading {paper.title}: {e}")
            return {
                "title": paper.title,
                "authors": [str(author) for author in paper.authors],
                "summary": "Error: Could not download paper",
                "url": paper.entry_id,
                "published": paper.published
            }
        
        # Extract text from PDF using the PDFProcessor
        try:
            text = PDFProcessor.extract_text_from_file(pdf_path)
            text = PDFProcessor.clean_text(text)
        except Exception as e:
            print(f"Error processing {paper.title}: {e}")
            return {
                "title": paper.title,
                "authors": [str(author) for author in paper.authors],
                "summary": "Error: Could not process PDF",
                "url": paper.entry_id,
                "published": paper.published
            }
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create summary
        summary_prompt = PromptTemplate.from_template(
            "Summarize the following scientific paper excerpt:\n\n{text}\n\nSummary:"
        )
        
        chain = summary_prompt | self.llm | StrOutputParser()
        summary = chain.invoke({"text": "\n".join(chunks[:3])})  # Summarize first few chunks
        
        return {
            "title": paper.title,
            "authors": [str(author) for author in paper.authors],
            "summary": summary,
            "url": paper.entry_id,
            "published": paper.published
        }

    def _extract_text_from_pdf(self, pdf_url: str) -> str:
        from utils.pdf_processor import PDFProcessor
        pdf_content = PDFProcessor.download_pdf(pdf_url)
        text = PDFProcessor.extract_text(pdf_content)
        return PDFProcessor.clean_text(text)

    def summarize_topic(self, topic: str, max_papers: int = 5) -> List[Dict]:
        papers = self.search_papers(topic, max_papers)
        summaries = []
        
        for paper in papers:
            summary = self.process_paper(paper)
            summaries.append(summary)
            
        return summaries 