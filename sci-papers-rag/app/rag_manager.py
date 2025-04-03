from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
import chromadb
import os
from typing import List, Dict
import json

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
        chroma_dir = os.path.join(data_dir, "chromadb")
        os.makedirs(chroma_dir, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_dir)
        self.vector_store = None
        self.conversation_chain = None
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"  # Add this to match the chain's output
        )

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
        documents = []
        print(f"\nProcessing {len(paper_ids)} papers: {paper_ids}")
        
        for paper_id in paper_ids:
            print(f"\nLoading paper {paper_id}...")
            paper = self._load_paper_content(paper_id)
            
            if paper and paper['content']:
                print(f"Splitting content for paper: {paper['title']}")
                # Split content into chunks
                chunks = self.text_splitter.split_text(paper['content'])
                print(f"Created {len(chunks)} chunks")
                
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
                    documents.append(doc)
            else:
                print(f"Skipping paper {paper_id}: No content available")

        print(f"\nTotal documents created: {len(documents)}")
        if not documents:
            raise ValueError("No valid documents to process. Make sure papers have both metadata and content files.")

        print("Creating vector store...")
        # Create vector store
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=os.path.join(self.data_dir, "chromadb")
        )

        print("Creating conversation chain...")
        # Create conversation chain
        self._create_conversation_chain()

    def _create_conversation_chain(self):
        """Create the conversation chain with custom prompt"""
        custom_template = """You are a helpful research assistant. Use the following pieces of context from research papers to answer the question. If you don't know the answer, just say that you don't know. Don't try to make up an answer.

Context: {context}

Chat History: {chat_history}

Question: {question}

Answer: Let me help you understand this based on the research papers:"""

        CUSTOM_PROMPT = PromptTemplate(
            template=custom_template,
            input_variables=["context", "chat_history", "question"]
        )

        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(temperature=0.7, model="gpt-4"),
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 4}
            ),
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": CUSTOM_PROMPT},
            return_source_documents=True,
            verbose=True  # Add this for debugging
        )

    def chat(self, message: str) -> Dict:
        """Process a chat message and return response with sources"""
        if not self.conversation_chain:
            return {
                "answer": "Please select papers first to start the conversation.",
                "sources": []
            }

        try:
            result = self.conversation_chain({"question": message})
            
            # Extract source information and deduplicate by paper_id
            seen_papers = set()
            sources = []
            
            for doc in result.get("source_documents", []):
                if hasattr(doc, 'metadata'):
                    paper_id = doc.metadata.get("paper_id")
                    title = doc.metadata.get("title")
                    
                    # Only add if we haven't seen this paper yet
                    if paper_id and title and paper_id not in seen_papers:
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