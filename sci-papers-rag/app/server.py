from flask import Flask, render_template, jsonify, request, redirect
from arxiv_paper_summarizer import ArxivPaperSummarizer
import logging

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
    summaries = summarizer.search_papers(topic, max_papers=4)
    return jsonify({
        'summaries': summaries,
        'papers': summarizer.get_stored_papers()
    })

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

if __name__ == '__main__':
    # Remove debug=True to disable Flask's debug mode
    app.run() 