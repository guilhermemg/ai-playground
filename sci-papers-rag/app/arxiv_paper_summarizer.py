from typing import List, Dict
import arxiv
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from utils.pdf_processor import PDFProcessor
import os
import json
from openai import OpenAI

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
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def get_stored_papers(self) -> List[Dict]:
        """Get list of papers stored locally with their metadata"""
        papers = []
        for file in os.listdir(self.data_dir):
            if file.endswith('.pdf'):
                paper_id = file.replace('.pdf', '')
                # Try to get metadata from JSON
                paper_info = self.get_paper_metadata(paper_id)
                
                if not paper_info:
                    # If no metadata, create basic info from filename
                    paper_info = {
                        "id": paper_id,
                        "title": f"Paper {paper_id}",
                        "authors": [],
                        "summary": "Click to generate summary",
                        "published": "",
                    }
                
                # Ensure ID is always present
                if 'id' not in paper_info:
                    paper_info['id'] = paper_id
                    
                papers.append(paper_info)
        
        return papers

    def get_paper_metadata(self, paper_id: str) -> Dict:
        """Get metadata for a specific paper"""
        metadata_file = os.path.join(self.data_dir, f"{paper_id}.json")
        pdf_file = os.path.join(self.data_dir, f"{paper_id}.pdf")
        
        try:
            # First try to get existing metadata
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    return json.load(f)
            
            # If metadata doesn't exist but PDF does, generate it
            if os.path.exists(pdf_file):
                try:
                    print(f"Generating new summary for {paper_id}")
                    # Extract text from PDF
                    text = PDFProcessor.extract_text_from_file(pdf_file)
                    text = PDFProcessor.clean_text(text)
                    
                    # Generate summary
                    chunks = self.text_splitter.split_text(text)
                    summary = self._generate_summary("\n".join(chunks[:3]))
                    
                    # Try to get paper info from arXiv
                    try:
                        # Clean paper_id to match arXiv format (remove file extension if present)
                        clean_id = paper_id.replace('.pdf', '')
                        client = arxiv.Client()
                        paper = next(client.results(arxiv.Search(id_list=[clean_id])))
                        metadata = {
                            "id": paper_id,
                            "title": paper.title,
                            "authors": [str(author) for author in paper.authors],
                            "summary": summary,
                            "url": paper.entry_id,
                            "published": paper.published.isoformat() if paper.published else "",
                            "pdf_url": paper.pdf_url,
                            "categories": paper.categories,
                            "comment": paper.comment,
                            "journal_ref": paper.journal_ref,
                            "doi": paper.doi
                        }
                    except Exception as e:
                        print(f"Could not fetch paper info from arXiv: {e}")
                        # Fallback to basic metadata with generated summary
                        metadata = {
                            "id": paper_id,
                            "title": f"Paper {paper_id}",
                            "authors": [],
                            "summary": summary,
                            "url": f"https://arxiv.org/abs/{clean_id}",
                            "published": "",
                            "pdf_url": f"https://arxiv.org/pdf/{clean_id}.pdf"
                        }
                    
                    # Save metadata
                    self._save_metadata(paper_id, metadata)
                    return metadata
                    
                except Exception as e:
                    print(f"Error generating summary from PDF: {e}")
                    return {
                        "id": paper_id,
                        "title": f"Paper {paper_id}",
                        "authors": [],
                        "summary": "Error: Could not generate summary from PDF",
                        "url": "",
                        "published": "",
                        "error": True
                    }
            
            print(f"No PDF found for {paper_id}")
            return {
                "id": paper_id,
                "title": f"Paper {paper_id}",
                "authors": [],
                "summary": f"No PDF found for paper {paper_id}",
                "url": "",
                "published": "",
                "error": True
            }
            
        except Exception as e:
            print(f"Unexpected error processing {paper_id}: {e}")
            return {
                "id": paper_id,
                "title": f"Paper {paper_id}",
                "authors": [],
                "summary": "An unexpected error occurred while processing this paper",
                "url": "",
                "published": "",
                "error": True
            }

    def search_papers(self, topic: str, max_results: int = 5) -> List[Dict]:
        """Search and process papers from arXiv"""
        client = arxiv.Client()
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
        )
        papers = list(client.results(search))
        return [self.process_paper(paper) for paper in papers]

    def process_paper(self, paper: arxiv.Result) -> Dict:
        """Process a single paper and return its metadata"""
        paper_id = paper.get_short_id()
        pdf_path = os.path.join(self.data_dir, f"{paper_id}.pdf")
        
        try:
            # Download PDF
            pdf_content = PDFProcessor.download_pdf(paper.pdf_url)
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            # Extract and process text
            text = PDFProcessor.extract_text_from_file(pdf_path)
            text = PDFProcessor.clean_text(text)
            summary = self._generate_summary_from_text(text)
            
            metadata = {
                "id": paper_id,
                "title": paper.title,
                "authors": [str(author) for author in paper.authors],
                "summary": summary,
                "url": paper.entry_id,
                "published": paper.published.isoformat(),
                "pdf_url": paper.pdf_url,
                "categories": paper.categories,
                "comment": paper.comment,
                "journal_ref": paper.journal_ref,
                "doi": paper.doi
            }
            
            self._save_metadata(paper_id, metadata)
            return metadata
            
        except Exception as e:
            print(f"Error processing {paper.title}: {e}")
            return {
                "id": paper_id,
                "title": paper.title,
                "authors": [str(author) for author in paper.authors],
                "summary": "Error: Could not process paper",
                "url": paper.entry_id,
                "published": paper.published.isoformat() if paper.published else "",
                "error": True
            }

    def _generate_summary_from_text(self, text: str) -> str:
        """Generate a summary from text content"""
        chunks = self.text_splitter.split_text(text)
        return self._generate_summary("\n".join(chunks[:3]))

    def _generate_summary(self, text: str) -> str:
        """Generate a summary using LLM"""
        summary_prompt = PromptTemplate.from_template(
            "Summarize the following scientific paper excerpt:\n\n{text}\n\nSummary:"
        )
        chain = summary_prompt | self.llm | StrOutputParser()
        return chain.invoke({"text": text})

    def _save_metadata(self, paper_id: str, metadata: Dict) -> None:
        """Save paper metadata to JSON file"""
        metadata_file = os.path.join(self.data_dir, f"{paper_id}.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def reprocess_all_papers(self) -> List[Dict]:
        """Reprocess all PDFs and regenerate their metadata"""
        results = []
        
        # Get all PDF files
        pdf_files = [f for f in os.listdir(self.data_dir) if f.endswith('.pdf')]
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            paper_id = pdf_file.replace('.pdf', '')
            print(f"\nProcessing {paper_id}...")
            
            try:
                # Clean paper_id to match arXiv format
                clean_id = paper_id.replace('.pdf', '')
                
                # Try to get paper info from arXiv
                try:
                    client = arxiv.Client()
                    paper = next(client.results(arxiv.Search(id_list=[clean_id])))
                    
                    # Extract and process text
                    pdf_path = os.path.join(self.data_dir, pdf_file)
                    text = PDFProcessor.extract_text_from_file(pdf_path)
                    text = PDFProcessor.clean_text(text)
                    
                    # Generate summary
                    chunks = self.text_splitter.split_text(text)
                    summary = self._generate_summary("\n".join(chunks[:3]))
                    
                    metadata = {
                        "id": paper_id,
                        "title": paper.title,
                        "authors": [str(author) for author in paper.authors],
                        "summary": summary,
                        "url": paper.entry_id,
                        "published": paper.published.isoformat() if paper.published else "",
                        "pdf_url": paper.pdf_url,
                        "categories": paper.categories,
                        "comment": paper.comment,
                        "journal_ref": paper.journal_ref,
                        "doi": paper.doi
                    }
                    
                    # Save metadata
                    self._save_metadata(paper_id, metadata)
                    results.append(metadata)
                    print(f"✓ Successfully processed {paper_id}")
                    
                except Exception as e:
                    print(f"× Error processing {paper_id}: {e}")
                    results.append({
                        "id": paper_id,
                        "error": str(e)
                    })
                    
            except Exception as e:
                print(f"× Unexpected error for {paper_id}: {e}")
                results.append({
                    "id": paper_id,
                    "error": str(e)
                })
        
        print(f"\nProcessing complete. Processed {len(results)} papers.")
        return results 

    def process_paper_by_id(self, paper_id: str) -> Dict:
        """Process a paper by its arXiv ID"""
        try:
            # Get paper info from arXiv
            client = arxiv.Client()
            paper = next(client.results(arxiv.Search(id_list=[paper_id])))
            
            # Process the paper
            return self.process_paper(paper)
        except Exception as e:
            raise Exception(f"Error processing paper {paper_id}: {e}")

    def search_arxiv(self, topic: str, max_results: int = 5) -> List[Dict]:
        """Search arXiv and return paper metadata without downloading"""
        client = arxiv.Client()
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
        )
        papers = list(client.results(search))
        
        # Convert to simplified format without downloading PDFs
        return [{
            'entry_id': paper.entry_id,
            'title': paper.title,
            'authors': [str(author) for author in paper.authors],
            'summary': paper.summary,
            'published': paper.published.isoformat() if paper.published else None,
            'pdf_url': paper.pdf_url,
            'categories': paper.categories
        } for paper in papers]

    def search_local(self, query: str) -> List[Dict]:
        """Search papers in local storage"""
        query = query.lower()
        results = []
        
        for file in os.listdir(self.data_dir):
            if file.endswith('.json'):
                try:
                    with open(os.path.join(self.data_dir, file), 'r') as f:
                        paper = json.load(f)
                        # Search in title, summary, and authors
                        if (query in paper.get('title', '').lower() or
                            query in paper.get('summary', '').lower() or
                            any(query in author.lower() for author in paper.get('authors', []))):
                            results.append(paper)
                except Exception as e:
                    print(f"Error reading {file}: {e}")
                
        return results 

    def chat_about_papers(self, messages):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # or your preferred model
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in chat_about_papers: {str(e)}")
            raise

    def get_paper_by_id(self, paper_id):
        """Get paper data by ID from stored metadata"""
        try:
            # Get metadata from JSON file
            metadata_file = os.path.join(self.data_dir, f"{paper_id}.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Get PDF text if available
                pdf_file = os.path.join(self.data_dir, f"{paper_id}.pdf")
                content = None
                if os.path.exists(pdf_file):
                    text = PDFProcessor.extract_text_from_file(pdf_file)
                    content = PDFProcessor.clean_text(text)
                
                return {
                    'id': metadata.get('id'),
                    'title': metadata.get('title'),
                    'summary': metadata.get('summary'),
                    'content': content,
                    'authors': metadata.get('authors', []),
                    'published': metadata.get('published'),
                    'url': metadata.get('url'),
                    'pdf_url': metadata.get('pdf_url')
                }
            else:
                print(f"No metadata found for paper {paper_id}")
                return None
            
        except Exception as e:
            print(f"Error getting paper {paper_id}: {str(e)}")
            return None 