from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
import chromadb
import os
from typing import List, Dict, Set, Callable
import json
import hashlib
from langchain.schema import BaseRetriever
from pydantic import Field, BaseModel

class FilteredRetriever(BaseRetriever, BaseModel):
    """Retriever that filters documents based on allowed paper IDs."""
    
    base_retriever: BaseRetriever = Field(description="Base retriever to filter from")
    allowed_paper_ids: Set[str] = Field(description="Set of allowed paper IDs")

    class Config:
        arbitrary_types_allowed = True

    def get_relevant_documents(self, query: str) -> List[Document]:
        # Get documents from base retriever
        docs = self.base_retriever.get_relevant_documents(query)
        # Filter to only include documents from currently selected papers
        filtered_docs = [
            doc for doc in docs 
            if doc.metadata.get('paper_id') in self.allowed_paper_ids
        ]
        # Return top 4 filtered documents
        return filtered_docs[:4]
    
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        raise NotImplementedError("Async retrieval not implemented")

class RAGManager:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Create chromadb directory if it doesn't exist
        self.chroma_dir = os.path.join(data_dir, "chromadb")
        os.makedirs(self.chroma_dir, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)
        self.vector_store = None
        self.conversation_chain = None
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Load or create the processed papers tracking file
        self.processed_papers_file = os.path.join(self.chroma_dir, "processed_papers.json")
        self.processed_papers = self._load_processed_papers()
        self.current_papers = set()  # Add this to track currently selected papers

    def _load_processed_papers(self) -> Dict[str, str]:
        """Load the set of processed papers and their content hashes"""
        if os.path.exists(self.processed_papers_file):
            with open(self.processed_papers_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_processed_papers(self):
        """Save the set of processed papers"""
        with open(self.processed_papers_file, 'w') as f:
            json.dump(self.processed_papers, f)

    def _get_content_hash(self, content: str) -> str:
        """Generate a hash of the paper content to detect changes"""
        return hashlib.md5(content.encode()).hexdigest()

    def _load_paper_content(self, paper_id: str) -> Dict:
        """Load paper content and metadata from files"""
        try:
            metadata_file = os.path.join(self.data_dir, f"{paper_id}.json")
            print(f"Looking for metadata file: {metadata_file}")
            
            if not os.path.exists(metadata_file):
                print(f"Metadata file not found for paper {paper_id}")
                return None
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Get text content
            txt_file = os.path.join(self.data_dir, f"{paper_id}.txt")
            print(f"Looking for text file: {txt_file}")
            
            content = None
            if os.path.exists(txt_file):
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"Loaded content length: {len(content) if content else 0} characters")
            else:
                print(f"Text file not found for paper {paper_id}")
            
            paper_data = {
                'id': metadata['id'],
                'title': metadata['title'],
                'content': content,
                'summary': metadata['summary']
            }
            
            print(f"Loaded paper data for {paper_id}: {paper_data['title']}")
            return paper_data
            
        except Exception as e:
            print(f"Error loading paper {paper_id}: {str(e)}")
            return None

    def create_vector_store(self, paper_ids: List[str]):
        """Create or update vector store for selected papers"""
        print(f"Creating vector store for {len(paper_ids)} papers")

        # Store current paper selection
        self.current_papers = set(paper_ids)
        
        # Initialize vector store if not already done
        if not self.vector_store:
            self.vector_store = Chroma(
                persist_directory=self.chroma_dir,
                embedding_function=self.embeddings
            )

        new_documents = []
        
        for paper_id in paper_ids:
            paper = self._load_paper_content(paper_id)
            if paper and paper['content']:
                content_hash = self._get_content_hash(paper['content'])
                
                # Check if paper needs to be processed
                if (paper_id not in self.processed_papers or 
                    self.processed_papers[paper_id] != content_hash):
                    print(f"Processing new or updated paper: {paper_id}")
                    
                    # Split content into chunks
                    chunks = self.text_splitter.split_text(paper['content'])
                    
                    # Create Document objects with metadata
                    for i, chunk in enumerate(chunks):
                        doc = Document(
                            page_content=chunk,
                            metadata={
                                'paper_id': paper['id'],
                                'title': paper['title'],
                                'chunk_index': i,
                            }
                        )
                        new_documents.append(doc)
                    
                    # Update processed papers tracking
                    self.processed_papers[paper_id] = content_hash
                else:
                    print(f"Using cached embeddings for paper: {paper_id}")

        # Add new documents to vector store if any
        if new_documents:
            print(f"Adding {len(new_documents)} new chunks to vector store")
            self.vector_store.add_documents(new_documents)
            self._save_processed_papers()
        
        # Update text splitting parameters for better chunk quality
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Slightly smaller chunks for more precise retrieval
            chunk_overlap=150,  # Good overlap to maintain context
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],  # More granular splitting
        )

        # Create conversation chain
        self._create_conversation_chain()

    def _create_conversation_chain(self):
        """Create the conversation chain with custom prompt"""
        custom_template = """You are a knowledgeable research assistant with expertise in AI, machine learning, and computer science. Use both your general knowledge AND the specific information from the selected research papers to provide comprehensive answers.

First, consider the relevant context from the selected papers:

{context}

Then, combine this specific information with your general knowledge to provide a complete answer. Always ground your specific claims in the papers' content when available, but feel free to provide additional relevant context from your general knowledge.

Chat History: {chat_history}

Question: {question}

Answer: Let me help you understand this by combining the papers' specific findings with relevant background knowledge:"""

        CUSTOM_PROMPT = PromptTemplate(
            template=custom_template,
            input_variables=["context", "chat_history", "question"]
        )

        # Create base retriever with better search parameters
        base_retriever = self.vector_store.as_retriever(
            search_type="mmr",  # Use Maximum Marginal Relevance for better diversity
            search_kwargs={
                "k": 12,  # Retrieve more documents initially
                "fetch_k": 20,  # Consider a larger initial set
                "lambda_mult": 0.7  # Balance between relevance and diversity
            }
        )

        # Create filtered retriever
        filtered_retriever = FilteredRetriever(
            base_retriever=base_retriever,
            allowed_paper_ids=self.current_papers
        )

        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(
                temperature=0.7,
                model="gpt-4",
                model_kwargs={"top_p": 0.9}  # Add some variability while maintaining quality
            ),
            retriever=filtered_retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={
                "prompt": CUSTOM_PROMPT,
                "document_separator": "\n\nNext excerpt:\n",  # Better separation between chunks
            },
            return_source_documents=True,
            verbose=True
        )

    def chat(self, message: str) -> Dict:
        """Process a chat message and return response with sources"""
        if not self.current_papers:
            return {
                "answer": "Please select papers first to start the conversation. You can select papers from the collections panel.",
                "sources": []
            }

        if not self.conversation_chain:
            return {
                "answer": "Please select papers first to start the conversation.",
                "sources": []
            }

        try:
            result = self.conversation_chain({"question": message})
            
            # Extract source information and deduplicate
            seen_papers = set()
            sources = []
            
            for doc in result.get("source_documents", []):
                if hasattr(doc, 'metadata'):
                    paper_id = doc.metadata.get("paper_id")
                    title = doc.metadata.get("title")
                    
                    # Verify the source is from a currently selected paper
                    if (paper_id and title and 
                        paper_id in self.current_papers and 
                        paper_id not in seen_papers):
                        seen_papers.add(paper_id)
                        sources.append({
                            "title": title,
                            "paper_id": paper_id,
                            "chunk_index": doc.metadata.get("chunk_index")
                        })

            return {
                "answer": result["answer"],
                "sources": sources
            }
        except Exception as e:
            print(f"Error in chat: {e}")
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "sources": []
            } 