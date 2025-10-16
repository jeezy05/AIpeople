# Quick Setup Guide

## Prerequisites Check

Before starting, ensure you have:

1. **Docker Desktop** installed and **RUNNING**
   - Download from: https://www.docker.com/products/docker-desktop
   - Ensure the Docker Desktop application is started (you should see the Docker icon in your system tray)
   - Wait for it to show "Docker Desktop is running"

2. **Verify Docker is Running**:
   ```powershell
   docker --version
   docker info
   ```
   
   If you see an error about "pipe/dockerDesktopLinuxEngine", Docker Desktop is not running. Start it first!

## Step-by-Step Setup

### 1. Start Docker Desktop

1. Launch Docker Desktop application
2. Wait for it to fully start (status should show "Running")
3. Verify with: `docker info`

### 2. Build and Start All Services

Open PowerShell in the project directory and run:

```powershell
cd C:\Users\CHEEZYJEEZY\Desktop\Learnings\AIpeople
docker-compose up --build
```

**What to expect**:
- First build takes 3-5 minutes
- You'll see logs from all services
- Wait for message: "Kong Configuration Complete!"
- Services starting order:
  1. PostgreSQL database for Kong
  2. Kong database migrations
  3. Kong API Gateway
  4. Microservices (Policy, Retriever, Processor, Orchestrator)
  5. Kong setup (configures routes, auth, rate limiting)

### 3. Verify Services Are Running

Open a new PowerShell window and check:

```powershell
# Check all containers
docker-compose ps

# Should show all services as "running"
```

### 4. Test the API

#### Basic Test (PowerShell):

```powershell
$headers = @{
    "X-API-KEY" = "my-secret-api-key-12345"
    "Content-Type" = "application/json"
}

$body = @{
    request_id = "test-001"
    query = "machine learning"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/process-request" -Headers $headers -Body $body | ConvertTo-Json
```

#### Run Full Test Suite:

```powershell
.\test-api.ps1
```

### 5. View Logs

```powershell
# View all logs
docker-compose logs

# View specific service
docker-compose logs orchestrator
docker-compose logs kong

# View audit logs
Get-Content logs\audit.jsonl
```

### 6. Stop Services

```powershell
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Troubleshooting

### Issue: "pipe/dockerDesktopLinuxEngine: The system cannot find the file specified"

**Solution**: Docker Desktop is not running. Start Docker Desktop application and wait for it to fully initialize.

### Issue: Port already in use

**Solution**: Stop any services using ports 5000-5003, 8000-8001, 5432

```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill process by PID if needed
Stop-Process -Id <PID> -Force
```

### Issue: Services not starting

**Solution**: Check logs for specific service

```powershell
docker-compose logs <service-name>
```

### Issue: Kong not configured

**Solution**: Manually run Kong setup

```powershell
docker-compose up kong-setup
```

### Issue: Permission denied on logs directory

**Solution**: Ensure logs directory exists

```powershell
New-Item -ItemType Directory -Force -Path logs
```

## Quick Reference

### Service URLs

- **Kong Gateway (Public)**: http://localhost:8000
- **Kong Admin API**: http://localhost:8001
- **Orchestrator** (internal): http://localhost:5000
- **Policy Service** (internal): http://localhost:5001
- **Retriever Agent** (internal): http://localhost:5002
- **Processor Agent** (internal): http://localhost:5003

### API Key

Default API Key: `my-secret-api-key-12345`

### Request Format

```json
POST http://localhost:8000/process-request
Headers:
  X-API-KEY: my-secret-api-key-12345
  Content-Type: application/json

Body:
{
  "request_id": "unique-id",
  "query": "your search query"
}
```

### Response Format

```json
{
  "request_id": "unique-id",
  "trace_id": "generated-trace-id",
  "summary": "Document summary...",
  "label": "CATEGORY_LABEL",
  "document_count": 2
}
```

## Next Steps

1. ✅ Start Docker Desktop
2. ✅ Run `docker-compose up --build`
3. ✅ Wait for "Kong Configuration Complete!"
4. ✅ Test with `.\test-api.ps1`
5. ✅ Check `logs\audit.jsonl` for request traces

## Support

If you encounter issues:
1. Check Docker Desktop is running
2. View service logs: `docker-compose logs [service]`
3. Check audit logs: `logs\audit.jsonl`
4. Restart services: `docker-compose restart`

---

**Ready to go?** Start Docker Desktop, then run: `docker-compose up --build`


