#!/bin/bash

# API Configuration
API_KEY="my-secret-api-key-12345"
BASE_URL="http://localhost:8000"

echo "=============================================="
echo "  AI Microservices API Testing Suite"
echo "=============================================="
echo ""

# Test 1: Valid Request
echo "Test 1: Valid Request - Machine Learning Query"
echo "----------------------------------------------"
curl -s -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-001", "query": "machine learning"}' | python -m json.tool
echo ""
echo ""

# Test 2: Policy Denial
echo "Test 2: Policy Denial - Forbidden Word"
echo "----------------------------------------------"
curl -s -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-002", "query": "this is a forbidden topic"}' | python -m json.tool
echo ""
echo ""

# Test 3: Idempotency
echo "Test 3: Idempotency - Same request_id twice"
echo "----------------------------------------------"
echo "First request:"
curl -s -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-duplicate", "query": "cloud computing"}' | python -m json.tool
echo ""
echo "Second request (should return cached):"
curl -s -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-duplicate", "query": "cloud computing"}' | python -m json.tool
echo ""
echo ""

# Test 4: Different Topics
echo "Test 4: DevOps Query"
echo "----------------------------------------------"
curl -s -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-004", "query": "docker kubernetes containers"}' | python -m json.tool
echo ""
echo ""

# Test 5: API Design Query
echo "Test 5: API Architecture Query"
echo "----------------------------------------------"
curl -s -X POST $BASE_URL/process-request \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-005", "query": "microservices API gateway REST"}' | python -m json.tool
echo ""
echo ""

# Test 6: Invalid API Key
echo "Test 6: Authentication Failure - Invalid API Key"
echo "----------------------------------------------"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST $BASE_URL/process-request \
  -H "X-API-KEY: invalid-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test-006", "query": "test"}'
echo ""
echo ""

# Test 7: Rate Limiting
echo "Test 7: Rate Limiting - 6 requests (limit is 5/min)"
echo "----------------------------------------------"
for i in {1..6}; do
  echo "Request $i:"
  response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST $BASE_URL/process-request \
    -H "X-API-KEY: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"request_id\": \"test-rate-$i\", \"query\": \"test $i\"}")
  
  http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d: -f2)
  body=$(echo "$response" | sed '/HTTP_STATUS/d')
  
  if [ "$http_status" == "429" ]; then
    echo "  ❌ Rate limit exceeded (HTTP 429) - Expected!"
  else
    echo "  ✅ Request successful (HTTP $http_status)"
  fi
  echo ""
done

echo "=============================================="
echo "  Testing Complete!"
echo "=============================================="
echo ""
echo "Check logs/audit.jsonl for detailed traces"


