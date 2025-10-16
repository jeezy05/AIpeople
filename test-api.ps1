# PowerShell Test Script for AI Microservices API

$API_KEY = "my-secret-api-key-12345"
$BASE_URL = "http://localhost:8000"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  AI Microservices API Testing Suite" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Valid Request
Write-Host "Test 1: Valid Request - Machine Learning Query" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method Post -Uri "$BASE_URL/process-request" `
        -Headers @{"X-API-KEY"=$API_KEY; "Content-Type"="application/json"} `
        -Body '{"request_id": "test-001", "query": "machine learning"}'
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Policy Denial
Write-Host "Test 2: Policy Denial - Forbidden Word" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method Post -Uri "$BASE_URL/process-request" `
        -Headers @{"X-API-KEY"=$API_KEY; "Content-Type"="application/json"} `
        -Body '{"request_id": "test-002", "query": "this is a forbidden topic"}'
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: Idempotency
Write-Host "Test 3: Idempotency - Same request_id twice" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow
Write-Host "First request:"
try {
    $response1 = Invoke-RestMethod -Method Post -Uri "$BASE_URL/process-request" `
        -Headers @{"X-API-KEY"=$API_KEY; "Content-Type"="application/json"} `
        -Body '{"request_id": "test-duplicate", "query": "cloud computing"}'
    $response1 | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""
Write-Host "Second request (should return cached):"
try {
    $response2 = Invoke-RestMethod -Method Post -Uri "$BASE_URL/process-request" `
        -Headers @{"X-API-KEY"=$API_KEY; "Content-Type"="application/json"} `
        -Body '{"request_id": "test-duplicate", "query": "cloud computing"}'
    $response2 | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: DevOps Query
Write-Host "Test 4: DevOps Query" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method Post -Uri "$BASE_URL/process-request" `
        -Headers @{"X-API-KEY"=$API_KEY; "Content-Type"="application/json"} `
        -Body '{"request_id": "test-004", "query": "docker kubernetes containers"}'
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: API Architecture Query
Write-Host "Test 5: API Architecture Query" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method Post -Uri "$BASE_URL/process-request" `
        -Headers @{"X-API-KEY"=$API_KEY; "Content-Type"="application/json"} `
        -Body '{"request_id": "test-005", "query": "microservices API gateway REST"}'
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 6: Invalid API Key
Write-Host "Test 6: Authentication Failure - Invalid API Key" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Method Post -Uri "$BASE_URL/process-request" `
        -Headers @{"X-API-KEY"="invalid-key-12345"; "Content-Type"="application/json"} `
        -Body '{"request_id": "test-006", "query": "test"}'
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Expected error (401 Unauthorized): $($_.Exception.Message)" -ForegroundColor Green
}
Write-Host ""

# Test 7: Rate Limiting
Write-Host "Test 7: Rate Limiting - 6 requests (limit is 5/min)" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow
for ($i = 1; $i -le 6; $i++) {
    Write-Host "Request $i:"
    try {
        $response = Invoke-RestMethod -Method Post -Uri "$BASE_URL/process-request" `
            -Headers @{"X-API-KEY"=$API_KEY; "Content-Type"="application/json"} `
            -Body "{`"request_id`": `"test-rate-$i`", `"query`": `"test $i`"}"
        Write-Host "  ✓ Request successful" -ForegroundColor Green
    } catch {
        if ($_.Exception.Response.StatusCode -eq 429) {
            Write-Host "  ✗ Rate limit exceeded (HTTP 429) - Expected!" -ForegroundColor Yellow
        } else {
            Write-Host "  Error: $_" -ForegroundColor Red
        }
    }
}
Write-Host ""

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Testing Complete!" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check logs\audit.jsonl for detailed traces" -ForegroundColor White


