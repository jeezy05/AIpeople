from flask import Flask, request, jsonify
import requests
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

# Service URLs
POLICY_SERVICE_URL = os.getenv('POLICY_SERVICE_URL', 'http://policy-service:5001')
RETRIEVER_SERVICE_URL = os.getenv('RETRIEVER_SERVICE_URL', 'http://retriever-agent:5002')
PROCESSOR_SERVICE_URL = os.getenv('PROCESSOR_SERVICE_URL', 'http://processor-agent:5003')

def log_audit(trace_id, request_id, endpoint, status, details):
    """Log request to audit.jsonl"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "orchestrator",
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
    return jsonify({"status": "healthy", "service": "orchestrator"}), 200

@app.route('/process-request', methods=['POST'])
def process_request():
    """Main orchestration endpoint"""
    data = request.get_json()
    
    # Generate trace_id for request tracking
    trace_id = str(uuid.uuid4())
    request_id = data.get('request_id')
    query = data.get('query', '')
    
    if not request_id:
        return jsonify({"error": "request_id is required"}), 400
    
    if not query:
        return jsonify({"error": "query is required"}), 400
    
    # Check for idempotency - return cached response if exists
    if request_id in request_cache:
        cached_response = request_cache[request_id]
        log_audit(trace_id, request_id, '/process-request', 'cached', {
            "query": query,
            "message": "Returned cached response"
        })
        return jsonify(cached_response), 200
    
    log_audit(trace_id, request_id, '/process-request', 'started', {"query": query})
    
    headers = {
        'X-Trace-ID': trace_id,
        'Content-Type': 'application/json'
    }
    
    try:
        # Step 1: Check Policy Service
        policy_response = requests.post(
            f'{POLICY_SERVICE_URL}/policy',
            json={"request_id": request_id, "query": query},
            headers=headers,
            timeout=5
        )
        
        if policy_response.status_code != 200:
            log_audit(trace_id, request_id, '/process-request', 'error', 
                     {"step": "policy", "error": "Policy service error"})
            return jsonify({"error": "Policy service error"}), 500
        
        policy_data = policy_response.json()
        
        if not policy_data.get('allowed', False):
            log_audit(trace_id, request_id, '/process-request', 'denied', 
                     {"reason": policy_data.get('reason', 'Policy denied')})
            return jsonify({
                "request_id": request_id,
                "trace_id": trace_id,
                "status": "denied",
                "reason": policy_data.get('reason', 'Policy denied')
            }), 403
        
        # Step 2: Call Retriever Agent
        retriever_response = requests.post(
            f'{RETRIEVER_SERVICE_URL}/retrieve',
            json={"request_id": request_id, "query": query},
            headers=headers,
            timeout=10
        )
        
        if retriever_response.status_code != 200:
            log_audit(trace_id, request_id, '/process-request', 'error', 
                     {"step": "retriever", "error": "Retriever service error"})
            return jsonify({"error": "Retriever service error"}), 500
        
        retriever_data = retriever_response.json()
        documents = retriever_data.get('documents', [])
        
        # Step 3: Call Processor Agent
        processor_response = requests.post(
            f'{PROCESSOR_SERVICE_URL}/process',
            json={
                "request_id": request_id,
                "query": query,
                "documents": documents
            },
            headers=headers,
            timeout=10
        )
        
        if processor_response.status_code != 200:
            log_audit(trace_id, request_id, '/process-request', 'error', 
                     {"step": "processor", "error": "Processor service error"})
            return jsonify({"error": "Processor service error"}), 500
        
        processor_data = processor_response.json()
        
        # Build final response
        response = {
            "request_id": request_id,
            "trace_id": trace_id,
            "summary": processor_data.get('summary', ''),
            "label": processor_data.get('label', ''),
            "document_count": processor_data.get('document_count', 0)
        }
        
        # Cache the response for idempotency
        request_cache[request_id] = response
        
        log_audit(trace_id, request_id, '/process-request', 'success', {
            "label": response['label'],
            "document_count": response['document_count']
        })
        
        return jsonify(response), 200
        
    except requests.exceptions.RequestException as e:
        log_audit(trace_id, request_id, '/process-request', 'error', 
                 {"error": str(e)})
        return jsonify({"error": f"Service communication error: {str(e)}"}), 500
    except Exception as e:
        log_audit(trace_id, request_id, '/process-request', 'error', 
                 {"error": str(e)})
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

