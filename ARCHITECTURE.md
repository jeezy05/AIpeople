# System Architecture Documentation

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENT APPLICATION                            │
│                                                                          │
│  Request: POST /process-request                                         │
│  Headers: X-API-KEY: my-secret-api-key-12345                           │
│  Body: { "request_id": "...", "query": "..." }                         │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               │ HTTP/JSON
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         KONG API GATEWAY                                 │
│                         (Port 8000/8001)                                │
├─────────────────────────────────────────────────────────────────────────┤
│  Plugins:                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 1. Key Authentication (X-API-KEY)                               │   │
│  │    - Validates API key                                          │   │
│  │    - Returns 401 if invalid                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 2. Rate Limiting                                                │   │
│  │    - 5 requests per minute                                      │   │
│  │    - Returns 429 if exceeded                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 3. File Logging                                                 │   │
│  │    - Logs all requests                                          │   │
│  │    - Path: /logs/kong-requests.log                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Database: PostgreSQL 13                                                │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               │ Routes to
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR SERVICE                                │
│                         (Port 5000)                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Responsibilities:                                                       │
│  • Generate unique trace_id                                             │
│  • Check idempotency cache                                              │
│  • Coordinate service calls                                             │
│  • Aggregate responses                                                  │
│  • Error handling                                                       │
│                                                                          │
│  Cache: In-memory dictionary                                            │
│  Key: request_id → Response                                             │
└─────┬──────────────┬──────────────┬─────────────────────────────────────┘
      │              │              │
      │ Step 1       │ Step 2       │ Step 3
      ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│   POLICY     │ │  RETRIEVER   │ │   PROCESSOR      │
│   SERVICE    │ │    AGENT     │ │    AGENT         │
│  (Port 5001) │ │  (Port 5002) │ │  (Port 5003)     │
├──────────────┤ ├──────────────┤ ├──────────────────┤
│              │ │              │ │                  │
│ POST /policy │ │ POST /retrieve│ │ POST /process   │
│              │ │              │ │                  │
│ Validates:   │ │ Searches:    │ │ Processes:       │
│ • Query      │ │ • 12 docs    │ │ • Summarizes     │
│   content    │ │ • Keyword    │ │ • Labels         │
│ • Forbidden  │ │   matching   │ │ • Caches         │
│   words      │ │ • Top 3      │ │                  │
│              │ │   results    │ │                  │
│ Returns:     │ │              │ │ Returns:         │
│ • allowed    │ │ Returns:     │ │ • summary        │
│ • reason     │ │ • documents  │ │ • label          │
│              │ │ • scores     │ │ • count          │
└──────┬───────┘ └──────┬───────┘ └────────┬─────────┘
       │                │                  │
       │                │                  │
       └────────────────┴──────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  AUDIT LOGGING   │
              │                  │
              │ logs/audit.jsonl │
              └──────────────────┘
```

## Service Communication Flow

### Successful Request Flow

```
1. CLIENT
   │
   └─► POST /process-request
       Header: X-API-KEY
       Body: {request_id, query}
       
2. KONG GATEWAY
   │
   ├─► Authenticate API Key
   │   └─► ✓ Valid
   │
   ├─► Check Rate Limit
   │   └─► ✓ Under limit (< 5/min)
   │
   ├─► Log Request
   │   └─► Write to kong-requests.log
   │
   └─► Forward to Orchestrator
   
3. ORCHESTRATOR
   │
   ├─► Generate trace_id: "abc-123"
   │
   ├─► Check Cache
   │   └─► request_id not found (new request)
   │
   ├─► Log: "started"
   │
   └─► Step 1: Call Policy Service
       │
       ├─► POST http://policy-service:5001/policy
       │   Header: X-Trace-ID: abc-123
       │   Body: {request_id, query}
       │
       └─► Response: {allowed: true, reason: "..."}
   
4. POLICY SERVICE
   │
   ├─► Validate query: "machine learning"
   │
   ├─► Check forbidden words
   │   └─► ✓ No matches
   │
   ├─► Log: "allowed"
   │   └─► Write to audit.jsonl
   │
   └─► Return: {allowed: true}
   
5. ORCHESTRATOR (continued)
   │
   └─► Step 2: Call Retriever Agent
       │
       ├─► POST http://retriever-agent:5002/retrieve
       │   Header: X-Trace-ID: abc-123
       │   Body: {request_id, query}
       │
       └─► Response: {documents: [...], count: 2}
   
6. RETRIEVER AGENT
   │
   ├─► Search documents.json
   │   └─► Query: "machine learning"
   │
   ├─► Calculate relevance scores
   │   └─► ML keywords in titles/content
   │
   ├─► Sort by score, take top 3
   │
   ├─► Log: "success, 2 documents found"
   │   └─► Write to audit.jsonl
   │
   └─► Return: {documents: [doc1, doc2]}
   
7. ORCHESTRATOR (continued)
   │
   └─► Step 3: Call Processor Agent
       │
       ├─► POST http://processor-agent:5003/process
       │   Header: X-Trace-ID: abc-123
       │   Body: {request_id, query, documents}
       │
       └─► Response: {summary, label, count}
   
8. PROCESSOR AGENT
   │
   ├─► Check idempotency cache
   │   └─► request_id not found
   │
   ├─► Summarize documents
   │   └─► Extract key sentences
   │
   ├─► Generate label
   │   └─► Based on categories: "ARTIFICIAL_INTELLIGENCE"
   │
   ├─► Cache response
   │   └─► Store by request_id
   │
   ├─► Log: "success"
   │   └─► Write to audit.jsonl
   │
   └─► Return: {summary, label, document_count: 2}
   
9. ORCHESTRATOR (final)
   │
   ├─► Aggregate response
   │   └─► {request_id, trace_id, summary, label, document_count}
   │
   ├─► Cache response
   │   └─► Store by request_id
   │
   ├─► Log: "success"
   │   └─► Write to audit.jsonl
   │
   └─► Return to Kong
   
10. KONG GATEWAY
    │
    ├─► Log response
    │
    └─► Return to Client
    
11. CLIENT
    │
    └─► Receives: {request_id, trace_id, summary, label, document_count}
```

### Denied Request Flow (Policy Violation)

```
1-3. [Same as above until Policy Service]

4. POLICY SERVICE
   │
   ├─► Validate query: "this is forbidden"
   │
   ├─► Check forbidden words
   │   └─► ✗ Match found: "forbidden"
   │
   ├─► Log: "denied"
   │   └─► Write to audit.jsonl
   │
   └─► Return: {allowed: false, reason: "Query contains forbidden word: 'forbidden'"}

5. ORCHESTRATOR
   │
   ├─► Receive: allowed = false
   │
   ├─► Log: "denied"
   │   └─► Write to audit.jsonl
   │
   ├─► Skip Retriever and Processor
   │
   └─► Return error response
       └─► {request_id, trace_id, status: "denied", reason: "..."}
       └─► HTTP 403 Forbidden

6. CLIENT
   │
   └─► Receives: 403 error with reason
```

### Idempotent Request Flow (Duplicate request_id)

```
1-3. [Same as successful flow]

4. ORCHESTRATOR
   │
   ├─► Check Cache
   │   └─► ✓ request_id found in cache
   │
   ├─► Log: "cached"
   │   └─► Write to audit.jsonl
   │
   └─► Return cached response
       └─► No service calls made
       └─► Same trace_id as original

5. CLIENT
   │
   └─► Receives: Identical response to first request
```

### Rate Limit Exceeded Flow

```
1. CLIENT
   │
   └─► POST /process-request (6th request in same minute)

2. KONG GATEWAY
   │
   ├─► Authenticate API Key
   │   └─► ✓ Valid
   │
   ├─► Check Rate Limit
   │   └─► ✗ Exceeded (5/min limit)
   │
   ├─► Log: "rate limit exceeded"
   │
   └─► Return: HTTP 429 Too Many Requests
       └─► Headers:
           X-RateLimit-Limit-Minute: 5
           X-RateLimit-Remaining-Minute: 0

3. ORCHESTRATOR
   │
   └─► Never reached (blocked at Kong)

4. CLIENT
   │
   └─► Receives: 429 error
       └─► Must wait for rate limit window to reset
```

## Data Structures

### Request Object

```json
{
  "request_id": "string (required, unique)",
  "query": "string (required)"
}
```

### Response Object (Success)

```json
{
  "request_id": "string",
  "trace_id": "uuid",
  "summary": "string",
  "label": "enum(ARTIFICIAL_INTELLIGENCE|CLOUD_COMPUTING|...)",
  "document_count": "integer"
}
```

### Response Object (Denied)

```json
{
  "request_id": "string",
  "trace_id": "uuid",
  "status": "denied",
  "reason": "string"
}
```

### Document Object

```json
{
  "id": "string",
  "title": "string",
  "content": "string",
  "category": "string",
  "score": "integer (retriever only)"
}
```

### Audit Log Entry

```json
{
  "timestamp": "ISO 8601 datetime",
  "service": "string (orchestrator|policy-service|retriever-agent|processor-agent)",
  "trace_id": "uuid",
  "request_id": "string",
  "endpoint": "string",
  "status": "string (started|success|error|denied|cached|allowed)",
  "details": {
    // Service-specific details
  }
}
```

## Service Specifications

### Orchestrator Service

**Technology**: Python 3.11, Flask 3.0, requests 2.31

**Endpoints**:
- `GET /health` - Health check
- `POST /process-request` - Main orchestration endpoint

**Environment Variables**:
- `PORT` - Listen port (default: 5000)
- `POLICY_SERVICE_URL` - Policy service URL
- `RETRIEVER_SERVICE_URL` - Retriever service URL
- `PROCESSOR_SERVICE_URL` - Processor service URL

**Features**:
- UUID-based trace_id generation
- In-memory response caching
- Sequential service orchestration
- Error handling and propagation
- Comprehensive logging

### Policy Service

**Technology**: Python 3.11, Flask 3.0

**Endpoints**:
- `GET /health` - Health check
- `POST /policy` - Policy validation

**Configuration**:
- Forbidden words: `['forbidden', 'banned', 'illegal']`
- Extensible for additional rules

**Logic**:
```python
for word in forbidden_words:
    if word.lower() in query.lower():
        return denied
return allowed
```

### Retriever Agent

**Technology**: Python 3.11, Flask 3.0

**Endpoints**:
- `GET /health` - Health check
- `POST /retrieve` - Document retrieval

**Data Source**: 
- `documents.json` - 12 documents across 8 categories

**Algorithm**:
```python
score = 0
for keyword in query.split():
    if keyword in document.content:
        score += 1
    if keyword in document.title:
        score += 2
return top_k(sorted_by_score)
```

### Processor Agent

**Technology**: Python 3.11, Flask 3.0

**Endpoints**:
- `GET /health` - Health check
- `POST /process` - Document processing

**Features**:
- Extractive summarization
- Category-based labeling
- In-memory response caching

**Label Mapping**:
```python
{
  "AI": "ARTIFICIAL_INTELLIGENCE",
  "Cloud": "CLOUD_COMPUTING",
  "Architecture": "SOFTWARE_ARCHITECTURE",
  "DevOps": "DEVOPS",
  "API": "API_DESIGN",
  "Programming": "PROGRAMMING",
  "Database": "DATABASE",
  "Security": "SECURITY"
}
```

## Deployment Architecture

```
Docker Compose
├── Network: microservices-net
│
├── Volume: kong-data (PostgreSQL data)
│
├── Bind Mount: ./logs → /app/logs (all services)
│
└── Services:
    ├── kong-database (postgres:13)
    │   └── Port: 5432 (internal)
    │
    ├── kong-migration (kong:3.4)
    │   └── Runs once, exits
    │
    ├── kong (kong:3.4)
    │   ├── Port: 8000 (proxy)
    │   └── Port: 8001 (admin)
    │
    ├── kong-setup (custom)
    │   └── Runs once, configures Kong
    │
    ├── policy-service (custom)
    │   └── Port: 5001
    │
    ├── retriever-agent (custom)
    │   └── Port: 5002
    │
    ├── processor-agent (custom)
    │   └── Port: 5003
    │
    └── orchestrator (custom)
        └── Port: 5000
```

## Security Layers

1. **Perimeter Security** (Kong)
   - API Key authentication
   - Rate limiting
   - Request validation

2. **Application Security**
   - Policy-based content filtering
   - Input validation
   - Error sanitization

3. **Operational Security**
   - Audit logging
   - Request tracing
   - Health monitoring

4. **Network Security**
   - Internal service network
   - No direct external access to services
   - Kong as single entry point

## Scalability Considerations

### Horizontal Scaling

Each service can be scaled independently:

```yaml
orchestrator:
  deploy:
    replicas: 3
  
retriever-agent:
  deploy:
    replicas: 5  # Scale based on query load
```

### Vertical Scaling

```yaml
orchestrator:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 1G
```

### Caching Strategy

- **Level 1**: Orchestrator cache (request_id → response)
- **Level 2**: Processor cache (request_id → processed result)
- **Level 3**: Kong cache (future enhancement)

### Load Balancing

Kong can load balance across multiple orchestrator instances:

```python
# Kong configuration
{
  "targets": [
    {"target": "orchestrator-1:5000"},
    {"target": "orchestrator-2:5000"},
    {"target": "orchestrator-3:5000"}
  ]
}
```

## Monitoring Points

1. **Kong Metrics**
   - Request count
   - Response times
   - Error rates
   - Rate limit hits

2. **Service Health**
   - /health endpoints
   - Service uptime
   - Error rates

3. **Audit Logs**
   - Request traces
   - Service communication
   - Error patterns

4. **Resource Usage**
   - CPU utilization
   - Memory usage
   - Network I/O

---

**This architecture provides**:
- ✅ Separation of concerns
- ✅ Single responsibility per service
- ✅ Scalability and resilience
- ✅ Comprehensive observability
- ✅ Security in depth


