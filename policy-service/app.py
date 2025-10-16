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

def log_audit(trace_id, request_id, endpoint, status, details):
    """Log request to audit.jsonl"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "policy-service",
        "trace_id": trace_id,
        "request_id": request_id,
        "endpoint": endpoint,
        "status": status,
        "details": details
    }
    
    with open('/app/logs/audit.jsonl', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "policy-service"}), 200

@app.route('/policy', methods=['POST'])
def check_policy():
    """Check if the request violates any policy"""
    data = request.get_json()
    
    trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))
    request_id = data.get('request_id', 'unknown')
    query = data.get('query', '')
    
    # Check for forbidden words
    forbidden_words = ['forbidden', 'banned', 'illegal']
    is_allowed = True
    reason = "Policy check passed"
    
    for word in forbidden_words:
        if word.lower() in query.lower():
            is_allowed = False
            reason = f"Query contains forbidden word: '{word}'"
            break
    
    status = "allowed" if is_allowed else "denied"
    
    log_audit(trace_id, request_id, '/policy', status, {
        "query": query,
        "reason": reason
    })
    
    response = {
        "allowed": is_allowed,
        "reason": reason,
        "request_id": request_id,
        "trace_id": trace_id
    }
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)

