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

# Load document database
with open('/app/documents.json', 'r') as f:
    DOCUMENTS = json.load(f)

def log_audit(trace_id, request_id, endpoint, status, details):
    """Log request to audit.jsonl"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "retriever-agent",
        "trace_id": trace_id,
        "request_id": request_id,
        "endpoint": endpoint,
        "status": status,
        "details": details
    }
    
    with open('/app/logs/audit.jsonl', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def search_documents(query, top_k=3):
    """Simple keyword-based search"""
    results = []
    query_lower = query.lower()
    
    for doc in DOCUMENTS:
        # Calculate simple relevance score based on keyword matches
        score = 0
        for word in query_lower.split():
            if word in doc['content'].lower():
                score += 1
            if word in doc['title'].lower():
                score += 2
        
        if score > 0:
            results.append({
                "id": doc['id'],
                "title": doc['title'],
                "content": doc['content'],
                "category": doc['category'],
                "score": score
            })
    
    # Sort by score and return top_k
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "retriever-agent"}), 200

@app.route('/retrieve', methods=['POST'])
def retrieve():
    """Retrieve top 3 matching documents"""
    data = request.get_json()
    
    trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))
    request_id = data.get('request_id', 'unknown')
    query = data.get('query', '')
    
    if not query:
        log_audit(trace_id, request_id, '/retrieve', 'error', {"error": "Query is required"})
        return jsonify({"error": "Query is required"}), 400
    
    # Search documents
    documents = search_documents(query, top_k=3)
    
    log_audit(trace_id, request_id, '/retrieve', 'success', {
        "query": query,
        "documents_found": len(documents)
    })
    
    response = {
        "request_id": request_id,
        "trace_id": trace_id,
        "query": query,
        "documents": documents,
        "count": len(documents)
    }
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)

