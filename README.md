# AI Microservices with API Gateway

A complete microservices architecture demonstrating API Gateway patterns with Kong, featuring three AI-powered services communicating via HTTP APIs with authentication, rate limiting, and policy enforcement.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Services](#services)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [API Usage](#api-usage)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Features](#features)
- [Logs and Monitoring](#logs-and-monitoring)

## 🏗️ Architecture Overview

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ POST /process-request
     │ X-API-KEY: my-secret-api-key-12345
     ▼
┌─────────────────────────────────────┐
│      Kong API Gateway               │
│  - Authentication (X-API-KEY)       │
│  - Rate Limiting (5 req/min)        │
│  - Request Logging                  │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│      Orchestrator Service           │
│  - Coordinates service calls        │
│  - Implements idempotency           │
│  - Tracks trace_id & request_id     │
└────┬────────────────────────────────┘
     │
     ├──1──► ┌─────────────────────┐
     │       │  Policy Service     │ ─── Checks for forbidden words
     │       └─────────────────────┘
     │
     ├──2──► ┌─────────────────────┐
     │       │  Retriever Agent    │ ─── Returns top 3 documents
     │       └─────────────────────┘
     │
     └──3──► ┌─────────────────────┐
             │  Processor Agent    │ ─── Summarizes & labels
             └─────────────────────┘
```

## 🔧 Services

### 1. **Kong API Gateway** (Port 8000)
   - **Purpose**: Entry point for all client requests
   - **Features**: 
     - API Key authentication (`X-API-KEY` header)
     - Rate limiting (5 requests/minute)
     - Request routing and logging
   - **Admin API**: Port 8001

### 2. **Orchestrator Service** (Port 5000)
   - **Purpose**: Coordinates the request flow between services
   - **Features**:
     - Implements idempotency (duplicate `request_id` returns cached response)
     - Generates and tracks `trace_id` for request tracing
     - Error handling and service communication

### 3. **Policy Service** (Port 5001)
   - **Purpose**: Validates requests against security policies
   - **Endpoint**: `POST /policy`
   - **Rules**: Denies requests containing words: `forbidden`, `banned`, `illegal`

### 4. **Retriever Agent** (Port 5002)
   - **Purpose**: Searches and retrieves relevant documents
   - **Endpoint**: `POST /retrieve`
   - **Features**: Returns top 3 matching documents from a knowledge base

### 5. **Processor Agent** (Port 5003)
   - **Purpose**: Processes and summarizes retrieved documents
   - **Endpoint**: `POST /process`
   - **Features**: Generates summary and assigns category label

## 📦 Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **curl** (for testing)

## 🚀 Quick Start

### 1. Clone and Navigate to Project

```bash
cd AIpeople
```

### 2. Start All Services

```bash
docker-compose up --build
```

**Note**: First startup takes 2-3 minutes as Kong initializes its database and all services build.

### 3. Verify Services Are Running

Wait for the message:
```
Kong Configuration Complete!
```

Check service health:
```bash
# Kong Gateway
curl http://localhost:8000/

# Individual services (if accessing directly)
curl http://localhost:5000/health  # Orchestrator
curl http://localhost:5001/health  # Policy Service
curl http://localhost:5002/health  # Retriever Agent
curl http://localhost:5003/health  # Processor Agent
```

## 🔌 API Usage

### Main Endpoint

**Endpoint**: `POST http://localhost:8000/process-request`

**Required Headers**:
- `X-API-KEY: my-secret-api-key-12345`
- `Content-Type: application/json`

**Request Body**:
```json
{
  "request_id": "req-001",
  "query": "machine learning"
}
```

**Response**:
```json
{
  "request_id": "req-001",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "Found 2 relevant document(s) in categories: AI. Key topics: Introduction to Machine Learning; Deep Learning Fundamentals. Summary: Machine learning is a subset of artificial intelligence...",
  "label": "ARTIFICIAL_INTELLIGENCE",
  "document_count": 2
}
```

### Sample curl Commands

#### 1. Basic Request
```bash
curl -X POST http://localhost:8000/process-request \
  -H "X-API-KEY: my-secret-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-001",
    "query": "machine learning"
  }'
```

#### 2. Test Idempotency (Same request_id returns cached result)
```bash
# First request
curl -X POST http://localhost:8000/process-request \
  -H "X-API-KEY: my-secret-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-duplicate-test",
    "query": "cloud computing"
  }'

# Second request with same request_id (returns cached)
curl -X POST http://localhost:8000/process-request \
  -H "X-API-KEY: my-secret-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-duplicate-test",
    "query": "cloud computing"
  }'
```

#### 3. Test Policy Denial (Query with "forbidden" word)
```bash
curl -X POST http://localhost:8000/process-request \
  -H "X-API-KEY: my-secret-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-forbidden",
    "query": "This is a forbidden query"
  }'
```

**Expected Response**:
```json
{
  "request_id": "req-forbidden",
  "trace_id": "...",
  "status": "denied",
  "reason": "Query contains forbidden word: 'forbidden'"
}
```

#### 4. Test Authentication Failure (Invalid API Key)
```bash
curl -X POST http://localhost:8000/process-request \
  -H "X-API-KEY: invalid-key" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-004",
    "query": "test"
  }'
```

**Expected Response**: `401 Unauthorized`

#### 5. Test Rate Limiting (Exceed 5 requests/minute)
```bash
# Run this command 6 times quickly
for i in {1..6}; do
  curl -X POST http://localhost:8000/process-request \
    -H "X-API-KEY: my-secret-api-key-12345" \
    -H "Content-Type: application/json" \
    -d "{\"request_id\": \"req-rate-$i\", \"query\": \"test $i\"}"
  echo ""
done
```

**Expected**: 6th request returns `429 Too Many Requests`

#### 6. Different Query Topics
```bash
# AI Query
curl -X POST http://localhost:8000/process-request \
  -H "X-API-KEY: my-secret-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-ai",
    "query": "deep learning neural networks"
  }'

# DevOps Query
curl -X POST http://localhost:8000/process-request \
  -H "X-API-KEY: my-secret-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-devops",
    "query": "docker kubernetes containers"
  }'

# Architecture Query
curl -X POST http://localhost:8000/process-request \
  -H "X-API-KEY: my-secret-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-arch",
    "query": "microservices API gateway"
  }'
```

## 🧪 Testing

### Windows PowerShell Commands

If using PowerShell on Windows, use these commands:

```powershell
# Basic Request
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/process-request" `
  -Headers @{"X-API-KEY"="my-secret-api-key-12345"; "Content-Type"="application/json"} `
  -Body '{"request_id": "req-001", "query": "machine learning"}' | ConvertTo-Json

# Test Policy Denial
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/process-request" `
  -Headers @{"X-API-KEY"="my-secret-api-key-12345"; "Content-Type"="application/json"} `
  -Body '{"request_id": "req-002", "query": "forbidden content"}' | ConvertTo-Json
```

### Automated Test Script

Create a test script `test-api.sh`:

```bash
#!/bin/bash

API_KEY="my-secret-api-key-12345"
BASE_URL="http://localhost:8000"

echo "Test 1: Valid Request"
curl -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-001", "query": "machine learning"}'

echo -e "\n\nTest 2: Policy Denial"
curl -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-002", "query": "forbidden topic"}'

echo -e "\n\nTest 3: Idempotency"
curl -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-duplicate", "query": "test"}'

curl -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-duplicate", "query": "test"}'
```

## 📁 Project Structure

```
AIpeople/
├── docker-compose.yml           # Main orchestration file
├── README.md                    # This file
├── logs/
│   └── audit.jsonl             # JSON logs with request traces
├── kong/
│   ├── Dockerfile              # Kong setup container
│   └── setup-kong.py           # Kong configuration script
├── orchestrator/
│   ├── Dockerfile
│   ├── app.py                  # Main orchestration logic
│   └── requirements.txt
├── policy-service/
│   ├── Dockerfile
│   ├── app.py                  # Policy validation service
│   └── requirements.txt
├── retriever-agent/
│   ├── Dockerfile
│   ├── app.py                  # Document retrieval service
│   ├── documents.json          # Knowledge base (12 documents)
│   └── requirements.txt
└── processor-agent/
    ├── Dockerfile
    ├── app.py                  # Document processing service
    └── requirements.txt
```

## ✨ Features

### 1. **API Gateway (Kong)**
   - ✅ Routes requests to backend services
   - ✅ API Key authentication via `X-API-KEY` header
   - ✅ Rate limiting: 5 requests/minute per consumer
   - ✅ Request/response logging
   - ✅ Centralized entry point

### 2. **Policy Enforcement**
   - ✅ Pre-processing validation
   - ✅ Content filtering (forbidden words)
   - ✅ Request denial with reason

### 3. **Request Tracing**
   - ✅ Unique `trace_id` per request flow
   - ✅ `request_id` for idempotency
   - ✅ Complete audit trail in JSON logs

### 4. **Idempotency**
   - ✅ Duplicate `request_id` returns cached response
   - ✅ Prevents duplicate processing
   - ✅ Consistent responses

### 5. **Service Communication**
   - ✅ HTTP REST APIs
   - ✅ JSON payloads
   - ✅ Error handling and propagation

### 6. **Logging & Monitoring**
   - ✅ Structured JSON logs (`audit.jsonl`)
   - ✅ Timestamp, service, trace_id, request_id tracking
   - ✅ Status and details per request

## 📊 Logs and Monitoring

### Audit Logs

All requests are logged to `logs/audit.jsonl` in JSON Lines format:

```json
{"timestamp": "2025-10-14T17:30:00.123456", "service": "orchestrator", "trace_id": "abc-123", "request_id": "req-001", "endpoint": "/process-request", "status": "started", "details": {"query": "machine learning"}}
{"timestamp": "2025-10-14T17:30:00.234567", "service": "policy-service", "trace_id": "abc-123", "request_id": "req-001", "endpoint": "/policy", "status": "allowed", "details": {"query": "machine learning", "reason": "Policy check passed"}}
{"timestamp": "2025-10-14T17:30:00.345678", "service": "retriever-agent", "trace_id": "abc-123", "request_id": "req-001", "endpoint": "/retrieve", "status": "success", "details": {"query": "machine learning", "documents_found": 2}}
{"timestamp": "2025-10-14T17:30:00.456789", "service": "processor-agent", "trace_id": "abc-123", "request_id": "req-001", "endpoint": "/process", "status": "success", "details": {"query": "machine learning", "documents_processed": 2, "label": "ARTIFICIAL_INTELLIGENCE"}}
{"timestamp": "2025-10-14T17:30:00.567890", "service": "orchestrator", "trace_id": "abc-123", "request_id": "req-001", "endpoint": "/process-request", "status": "success", "details": {"label": "ARTIFICIAL_INTELLIGENCE", "document_count": 2}}
```

### View Logs

```bash
# View all audit logs
cat logs/audit.jsonl

# Filter by service
cat logs/audit.jsonl | grep "orchestrator"

# Filter by request_id
cat logs/audit.jsonl | grep "req-001"

# Filter by trace_id
cat logs/audit.jsonl | grep "abc-123"

# View Kong logs
docker-compose logs kong

# View specific service logs
docker-compose logs orchestrator
docker-compose logs policy-service
docker-compose logs retriever-agent
docker-compose logs processor-agent
```

### PowerShell Log Commands

```powershell
# View audit logs
Get-Content logs\audit.jsonl

# Filter by service
Get-Content logs\audit.jsonl | Select-String "orchestrator"

# View Docker logs
docker-compose logs kong
docker-compose logs orchestrator
```

## 🛠️ Management Commands

### Start Services
```bash
docker-compose up --build
```

### Start in Background
```bash
docker-compose up -d --build
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove Volumes
```bash
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f orchestrator
```

### Restart Kong Configuration
```bash
docker-compose restart kong-setup
```

### Check Service Status
```bash
docker-compose ps
```

## 🔑 Configuration

### API Key

Default API Key: `my-secret-api-key-12345`

To create additional API keys:

```bash
# Access Kong admin API
curl -X POST http://localhost:8001/consumers/api-client/key-auth \
  -d "key=your-custom-api-key"
```

### Rate Limiting

Current: 5 requests/minute

To modify, edit `kong/setup-kong.py`:

```python
"config": {
    "minute": 10,  # Change to desired limit
    "policy": "local"
}
```

### Policy Rules

To add more forbidden words, edit `policy-service/app.py`:

```python
forbidden_words = ['forbidden', 'banned', 'illegal', 'your-word']
```

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check Docker daemon is running
docker info

# Check port availability
netstat -an | grep "8000\|5000\|5001\|5002\|5003"

# View detailed logs
docker-compose logs --tail=50
```

### Kong Not Configured

```bash
# Manually run Kong setup
docker-compose up kong-setup
```

### Audit Logs Not Appearing

```bash
# Ensure logs directory exists and has write permissions
mkdir -p logs
chmod 777 logs

# Check service volumes
docker-compose config
```

### Rate Limit Not Working

```bash
# Verify rate limiting plugin is enabled
curl http://localhost:8001/plugins | grep rate-limiting
```

## 📝 Notes

1. **First Startup**: Takes 2-3 minutes for Kong database initialization
2. **API Key**: Required for all requests via `X-API-KEY` header
3. **Idempotency**: Use unique `request_id` for new requests
4. **Rate Limits**: Tracked per minute, resets every 60 seconds
5. **Logs**: Persisted in `logs/audit.jsonl` with complete trace information

## 🎯 Assignment Deliverables Checklist

- ✅ 3-service architecture (Retriever, Processor, Policy)
- ✅ API Gateway (Kong) with routing
- ✅ Authentication (X-API-KEY)
- ✅ Rate limiting (5 req/min)
- ✅ Policy service integration
- ✅ Request tracing (trace_id, request_id)
- ✅ Idempotency support
- ✅ docker-compose.yml for local deployment
- ✅ JSON audit logs (logs/audit.jsonl)
- ✅ README.md with setup and curl commands
- ✅ Complete project structure

## 📧 Support

For issues or questions, check:
1. Service logs: `docker-compose logs [service-name]`
2. Kong admin API: http://localhost:8001
3. Audit logs: `logs/audit.jsonl`

---

**Built with**: Python, Flask, Kong API Gateway, Docker, PostgreSQL

**Author**: AI Microservices Team

**Date**: October 2025


