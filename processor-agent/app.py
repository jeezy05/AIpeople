from flask import Flask, request, jsonify
import logging
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# Setup logging
os.makedirs('/app/logs', exist_ok=True)
logging.basicConfig(level=logging.INFO)

# In-memory cache for idempotency
request_cache = {}

def log_audit(trace_id, request_id, endpoint, status, details):
    """Log request to audit.jsonl"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "processor-agent",
        "trace_id": trace_id,
        "request_id": request_id,
        "endpoint": endpoint,
        "status": status,
        "details": details
    }
    
    with open('/app/logs/audit.jsonl', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def summarize_documents(documents):
    """Create a summary from documents"""
    if not documents:
        return "No documents found to summarize."
    
    # Extract key information
    titles = [doc.get('title', 'Untitled') for doc in documents]
    categories = list(set([doc.get('category', 'Unknown') for doc in documents]))
    
    # Simple extractive summary - take first sentence from each document
    summaries = []
    for doc in documents:
        content = doc.get('content', '')
        first_sentence = content.split('.')[0] if content else ''
        if first_sentence:
            summaries.append(first_sentence.strip())
    
    summary = f"Found {len(documents)} relevant document(s) in categories: {', '.join(categories)}. "
    summary += "Key topics: " + "; ".join(titles[:3]) + ". "
    
    if summaries:
        summary += "Summary: " + " | ".join(summaries[:2])
    
    return summary

def generate_label(documents):
    """Generate a label based on document categories"""
    if not documents:
        return "NO_RESULTS"
    
    categories = [doc.get('category', 'Unknown') for doc in documents]
    most_common = max(set(categories), key=categories.count)
    
    label_map = {
        "AI": "ARTIFICIAL_INTELLIGENCE",
        "Cloud": "CLOUD_COMPUTING",
        "Architecture": "SOFTWARE_ARCHITECTURE",
        "DevOps": "DEVOPS",
        "API": "API_DESIGN",
        "Programming": "PROGRAMMING",
        "Database": "DATABASE",
        "Security": "SECURITY"
    }
    
    return label_map.get(most_common, "GENERAL")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "processor-agent"}), 200

@app.route('/process', methods=['POST'])
def process():
    """Process and summarize documents"""
    data = request.get_json()
    
    trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))
    request_id = data.get('request_id', 'unknown')
    documents = data.get('documents', [])
    query = data.get('query', '')
    
    # Check for idempotency - return cached response if exists
    if request_id in request_cache:
        cached_response = request_cache[request_id]
        log_audit(trace_id, request_id, '/process', 'cached', {
            "query": query,
            "message": "Returned cached response"
        })
        return jsonify(cached_response), 200
    
    # Process documents
    summary = summarize_documents(documents)
    label = generate_label(documents)
    
    log_audit(trace_id, request_id, '/process', 'success', {
        "query": query,
        "documents_processed": len(documents),
        "label": label
    })
    
    response = {
        "request_id": request_id,
        "trace_id": trace_id,
        "summary": summary,
        "label": label,
        "document_count": len(documents)
    }
    
    # Cache the response for idempotency
    request_cache[request_id] = response
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)

