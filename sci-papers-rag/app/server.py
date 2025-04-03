from flask import Flask, render_template, jsonify, request, redirect, send_from_directory
from arxiv_paper_summarizer import ArxivPaperSummarizer
import logging
import json

# Change logging level to ERROR to reduce verbosity
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = Flask(__name__)
summarizer = ArxivPaperSummarizer()

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
        
        if not message or not paper_ids:
            return jsonify({
                'error': True,
                'message': 'Message and selected papers are required'
            }), 400

        # Get papers content and context
        papers_context = []
        for paper_id in paper_ids:
            paper = summarizer.get_paper_by_id(paper_id)
            if paper:
                papers_context.append({
                    'title': paper['title'],
                    'summary': paper['summary'],
                    'content': paper.get('content')
                })

        if not papers_context:
            return jsonify({
                'error': True,
                'message': 'No valid papers found'
            }), 404

        # Prepare system message with papers context
        system_message = """You are a helpful AI research assistant. You have access to the following papers:
        
        {}
        
        Please help answer questions about these papers. Base your answers on the papers' content and summaries. 
        If you're unsure about something, say so.""".format(
            "\n\n".join([
                f"Paper: {p['title']}\nSummary: {p['summary']}\n" + 
                (f"Content: {p['content'][:1000]}..." if p['content'] else "")
                for p in papers_context
            ])
        )

        # Get response from chat model
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
        
        response = summarizer.chat_about_papers(messages)

        return jsonify({
            'response': response,
            'error': False
        })

    except Exception as e:
        print(f"Error processing chat: {str(e)}")
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