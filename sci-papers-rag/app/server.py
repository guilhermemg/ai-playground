from flask import Flask, render_template, jsonify, request, redirect, send_from_directory
from arxiv_paper_summarizer import ArxivPaperSummarizer
import logging
import json
import os
from rag_manager import RAGManager
from pdf_processor import PDFProcessor

# Change logging level to ERROR to reduce verbosity
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = Flask(__name__)
summarizer = ArxivPaperSummarizer()
rag_manager = RAGManager(os.path.join(os.path.dirname(__file__), "data"))

@app.route('/')
def home():
    papers = summarizer.get_stored_papers()
    return render_template('index.html', papers=papers)

@app.route('/papers')
def get_papers():
    papers = summarizer.get_stored_papers()
    return jsonify(papers)

@app.route('/search', methods=['POST'])
def search():
    topic = request.json.get('topic')
    search_type = request.json.get('search_type', 'arxiv')  # 'arxiv', 'local', or 'both'
    
    try:
        results = {
            'papers': [],
            'source': search_type
        }
        
        if search_type in ['arxiv', 'both']:
            arxiv_papers = summarizer.search_arxiv(topic, max_results=4)
            results['papers'].extend([{**p, 'source': 'arxiv'} for p in arxiv_papers])
            
        if search_type in ['local', 'both']:
            local_papers = summarizer.search_local(topic)
            results['papers'].extend([{**p, 'source': 'local'} for p in local_papers])
            
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500

@app.route('/paper_summary/', defaults={'paper_id': None})
@app.route('/paper_summary/<paper_id>')
def get_paper_summary(paper_id):
    if paper_id is None:
        return jsonify({
            "error": True,
            "summary": "No paper ID provided"
        })
    
    logger.debug(f"Received request for paper_id: {paper_id}")
    metadata = summarizer.get_paper_metadata(paper_id)
    logger.debug(f"Metadata result: {metadata is not None}")
    if metadata:
        return jsonify(metadata)
    
    return jsonify({
        "id": paper_id,
        "title": f"Paper {paper_id}",
        "authors": [],
        "summary": f"Summary not found for paper {paper_id}",
        "url": "",
        "published": "",
        "error": True
    })

@app.route('/process_paper/<paper_id>', methods=['POST'])
def process_paper(paper_id):
    paper_data = request.json
    try:
        # Process and summarize the paper
        result = summarizer.process_paper_by_id(paper_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "error": True,
            "message": str(e)
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message')
        paper_ids = data.get('paperIds', [])
        
        print(f"Received chat request with papers: {paper_ids}")
        print(f"Message: {message}")
        
        if not message or not paper_ids:
            return jsonify({
                'error': True,
                'message': 'Message and selected papers are required'
            }), 400

        # Process papers if needed and create txt files
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        for paper_id in paper_ids:
            pdf_file = os.path.join(data_dir, f"{paper_id}.pdf")
            txt_file = os.path.join(data_dir, f"{paper_id}.txt")
            
            # If we have the PDF but not the TXT, create it
            if os.path.exists(pdf_file) and not os.path.exists(txt_file):
                try:
                    # Extract text from PDF
                    text = PDFProcessor.extract_text_from_file(pdf_file)
                    cleaned_text = PDFProcessor.clean_text(text)
                    
                    # Save as TXT
                    with open(txt_file, 'w', encoding='utf-8') as f:
                        f.write(cleaned_text)
                    print(f"Created text file for {paper_id}")
                except Exception as e:
                    print(f"Error processing PDF for {paper_id}: {e}")
                    return jsonify({
                        'error': True,
                        'message': f'Error processing PDF for {paper_id}: {str(e)}'
                    }), 500

        # Check if all required files exist now
        missing_files = []
        for paper_id in paper_ids:
            metadata_file = os.path.join(data_dir, f"{paper_id}.json")
            txt_file = os.path.join(data_dir, f"{paper_id}.txt")
            
            if not os.path.exists(metadata_file):
                missing_files.append(f"{paper_id}.json")
            if not os.path.exists(txt_file):
                missing_files.append(f"{paper_id}.txt")
        
        if missing_files:
            return jsonify({
                'error': True,
                'message': f'Missing paper files: {", ".join(missing_files)}'
            }), 404

        # Create/update vector store for selected papers
        rag_manager.create_vector_store(paper_ids)

        # Get response from RAG system
        result = rag_manager.chat(message)

        return jsonify({
            'response': result['answer'],
            'sources': result['sources'],
            'error': False
        })

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'error': True,
            'message': f'Error processing chat: {str(e)}'
        }), 500

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Remove debug=True to disable Flask's debug mode
    app.run() 