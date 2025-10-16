# AI Microservices Architecture - Project Summary

## 🎯 Project Overview

A complete microservices architecture demonstrating API Gateway patterns using Kong, featuring three AI-powered services that communicate via HTTP APIs with authentication, rate limiting, policy enforcement, and comprehensive request tracing.

## ✅ Deliverables Status

| Requirement | Status | Implementation |
|------------|--------|----------------|
| 3-Service Architecture | ✅ Complete | Retriever, Processor, Policy services |
| API Gateway (Kong) | ✅ Complete | Kong 3.4 with PostgreSQL backend |
| Authentication | ✅ Complete | X-API-KEY header validation |
| Rate Limiting | ✅ Complete | 5 requests/minute |
| Policy Service | ✅ Complete | Pre-request validation, forbidden word detection |
| Request Tracing | ✅ Complete | trace_id and request_id tracking |
| Idempotency | ✅ Complete | Cached responses for duplicate request_ids |
| docker-compose.yml | ✅ Complete | Full orchestration with 8 services |
| JSON Audit Logs | ✅ Complete | logs/audit.jsonl with complete trace |
| README.md | ✅ Complete | Comprehensive documentation with curl examples |
| Test Scripts | ✅ Complete | Bash and PowerShell test suites |

## 📁 Project Structure

```
AIpeople/
├── docker-compose.yml           # Main orchestration (8 services)
├── README.md                    # Complete documentation
├── SETUP_GUIDE.md              # Quick start guide
├── PROJECT_SUMMARY.md          # This file
├── test-api.sh                 # Bash test script
├── test-api.ps1                # PowerShell test script
├── .gitignore                  # Git ignore rules
│
├── logs/
│   ├── .gitkeep               # Tracks logs directory
│   └── audit.jsonl            # Generated at runtime
│
├── kong/
│   ├── Dockerfile             # Kong setup container
│   └── setup-kong.py          # Automated Kong configuration
│
├── orchestrator/
│   ├── Dockerfile
│   ├── app.py                 # Main request orchestration
│   └── requirements.txt       # Flask, requests
│
├── policy-service/
│   ├── Dockerfile
│   ├── app.py                 # Policy validation logic
│   └── requirements.txt       # Flask
│
├── retriever-agent/
│   ├── Dockerfile
│   ├── app.py                 # Document retrieval
│   ├── documents.json         # Knowledge base (12 docs)
│   └── requirements.txt       # Flask
│
└── processor-agent/
    ├── Dockerfile
    ├── app.py                 # Document processing & summarization
    └── requirements.txt       # Flask
```

## 🏗️ Architecture Components

### 1. Kong API Gateway (Port 8000/8001)
- **Role**: Entry point, security, traffic management
- **Features**:
  - Service routing to orchestrator
  - API Key authentication via X-API-KEY header
  - Rate limiting: 5 requests/minute per consumer
  - Request/response logging
  - Admin API on port 8001
- **Database**: PostgreSQL 13
- **Configuration**: Automated via Python script

### 2. Orchestrator Service (Port 5000)
- **Role**: Coordinates multi-service request flow
- **Features**:
  - Generates unique trace_id for each request
  - Implements idempotency (caches by request_id)
  - Orchestrates: Policy → Retriever → Processor
  - Error handling and response aggregation
  - Comprehensive audit logging

### 3. Policy Service (Port 5001)
- **Role**: Pre-request validation
- **Endpoint**: POST /policy
- **Features**:
  - Validates query content
  - Denies requests with forbidden words: "forbidden", "banned", "illegal"
  - Returns allow/deny decision with reason
  - Logs all policy decisions

### 4. Retriever Agent (Port 5002)
- **Role**: Document search and retrieval
- **Endpoint**: POST /retrieve
- **Features**:
  - Searches 12-document knowledge base
  - Keyword-based relevance scoring
  - Returns top 3 matching documents
  - Categories: AI, Cloud, Architecture, DevOps, API, etc.

### 5. Processor Agent (Port 5003)
- **Role**: Document processing and summarization
- **Endpoint**: POST /process
- **Features**:
  - Extractive summarization
  - Category-based labeling
  - Idempotency support (separate cache)
  - Structured output with metadata

## 🔄 Request Flow

```
1. Client Request
   ↓
2. Kong Gateway
   - Validate API Key
   - Check Rate Limit
   - Log Request
   ↓
3. Orchestrator
   - Generate trace_id
   - Check idempotency cache
   ↓
4. Policy Service
   - Validate query content
   - Return allow/deny
   ↓
5. Retriever Agent (if allowed)
   - Search documents
   - Return top 3 matches
   ↓
6. Processor Agent
   - Summarize documents
   - Assign category label
   ↓
7. Response to Client
   {
     "request_id": "...",
     "trace_id": "...",
     "summary": "...",
     "label": "...",
     "document_count": 3
   }
```

## 📊 Logging & Tracing

### Audit Log Format (audit.jsonl)

Each line is a JSON object:

```json
{
  "timestamp": "2025-10-14T17:30:00.123456",
  "service": "orchestrator",
  "trace_id": "abc-123",
  "request_id": "req-001",
  "endpoint": "/process-request",
  "status": "success",
  "details": {
    "query": "machine learning",
    "label": "ARTIFICIAL_INTELLIGENCE",
    "document_count": 2
  }
}
```

### Trace Example

For a single request with trace_id `abc-123`:

1. **Orchestrator**: Request started
2. **Policy Service**: Policy check allowed
3. **Retriever Agent**: 2 documents found
4. **Processor Agent**: Documents processed
5. **Orchestrator**: Request completed

All logged with same trace_id for easy tracing.

## 🧪 Testing

### Test Scripts Provided

1. **test-api.sh** (Bash/Linux/Mac)
   - 7 comprehensive tests
   - Valid requests
   - Policy denial
   - Idempotency
   - Rate limiting
   - Authentication

2. **test-api.ps1** (PowerShell/Windows)
   - Same 7 tests as Bash version
   - Windows-native commands
   - Colored output

### Manual Testing

See README.md for detailed curl commands and PowerShell examples.

## 🔐 Security Features

1. **API Key Authentication**
   - Required X-API-KEY header
   - Enforced at gateway level
   - Invalid keys rejected with 401

2. **Rate Limiting**
   - 5 requests per minute per consumer
   - Prevents abuse
   - Returns 429 when exceeded

3. **Policy Enforcement**
   - Content validation before processing
   - Configurable forbidden words
   - Prevents malicious queries

4. **Request Tracing**
   - Every request logged
   - Full audit trail
   - Traceable across all services

## 🎯 Key Features

### Idempotency
- Duplicate `request_id` returns cached response
- Implemented at both orchestrator and processor levels
- Ensures consistent results for retries

### Distributed Tracing
- Unique `trace_id` per request
- Passed via X-Trace-ID header
- Logged by all services
- Enables end-to-end request tracking

### Service Independence
- Each service is self-contained
- Docker containerized
- Can be scaled independently
- Health check endpoints

### Error Handling
- Graceful degradation
- Informative error messages
- Proper HTTP status codes
- Error logging at each layer

## 📈 Performance Considerations

- **Rate Limiting**: Prevents overload (5 req/min)
- **Caching**: Idempotency reduces redundant processing
- **Async Ready**: Architecture supports async communication
- **Scalability**: Services can be replicated behind load balancer

## 🚀 Deployment

### Local Development
```bash
docker-compose up --build
```

### Production Considerations
1. **Environment Variables**: Externalize all configs
2. **Secrets Management**: Use Docker secrets or vault
3. **Load Balancing**: Add multiple instances of each service
4. **Monitoring**: Add Prometheus/Grafana
5. **Log Aggregation**: ELK stack or similar
6. **API Gateway**: Consider Kong Enterprise features

## 📚 Documentation Files

1. **README.md**: Main documentation with API usage
2. **SETUP_GUIDE.md**: Quick start guide
3. **PROJECT_SUMMARY.md**: This file - overview and deliverables
4. **Code Comments**: Inline documentation in all services

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| API Gateway | Kong | 3.4 |
| Database | PostgreSQL | 13 |
| Services | Python + Flask | 3.11 + 3.0 |
| Orchestration | Docker Compose | 2.x |
| HTTP Client | requests | 2.31 |

## 📋 API Endpoints Summary

| Service | Endpoint | Method | Purpose |
|---------|----------|--------|---------|
| Gateway | /process-request | POST | Main client endpoint |
| Orchestrator | /process-request | POST | Request orchestration |
| Policy | /policy | POST | Query validation |
| Retriever | /retrieve | POST | Document search |
| Processor | /process | POST | Summarization |
| All Services | /health | GET | Health check |

## 🎓 Learning Outcomes

This project demonstrates:

1. **Microservices Architecture**: Service decomposition and communication
2. **API Gateway Pattern**: Centralized routing, auth, and traffic management
3. **Service Orchestration**: Coordinating multiple service calls
4. **Security**: Authentication, rate limiting, policy enforcement
5. **Observability**: Logging, tracing, monitoring
6. **Idempotency**: Ensuring consistent results for retries
7. **Containerization**: Docker and Docker Compose
8. **RESTful APIs**: HTTP-based service communication

## ✨ Bonus Features

Beyond core requirements:

1. ✅ Comprehensive test scripts (Bash + PowerShell)
2. ✅ Health check endpoints for all services
3. ✅ Dual-level idempotency (orchestrator + processor)
4. ✅ Rich document knowledge base (12 documents, multiple categories)
5. ✅ Automated Kong configuration
6. ✅ Detailed setup guide
7. ✅ .gitignore for clean repository
8. ✅ Windows-specific PowerShell support

## 🔗 Google Drive Link

**Upload Instructions:**

1. Zip the entire `AIpeople` directory
2. Upload to Google Drive
3. Set sharing to "Anyone with the link can view"
4. Share the link

**What to include:**
- All source code files
- docker-compose.yml
- All documentation (README.md, etc.)
- Test scripts
- logs/.gitkeep (empty logs directory)

**Do NOT include:**
- logs/*.jsonl (generated at runtime)
- __pycache__/ directories
- Docker images or volumes

## 📞 Support

For issues:
1. Check SETUP_GUIDE.md
2. Review service logs: `docker-compose logs [service]`
3. Check audit logs: `logs/audit.jsonl`
4. Verify Docker Desktop is running

---

## ✅ Assignment Completion Checklist

- [x] 3-service architecture (Retriever, Processor, Policy)
- [x] API Gateway (Kong) with routing
- [x] X-API-KEY authentication
- [x] Rate limiting (5 req/min)
- [x] Policy service integration
- [x] Request tracing (trace_id, request_id)
- [x] Idempotency support
- [x] docker-compose.yml
- [x] JSON audit logs (logs/audit.jsonl)
- [x] README.md with setup & curl commands
- [x] Complete, working codebase

**Status**: ✅ **READY FOR SUBMISSION**

---

**Built**: October 14, 2025
**Author**: AI Development Team
**Assignment**: Deploy Microservices Behind an API Gateway


