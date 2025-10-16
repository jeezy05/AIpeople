#!/usr/bin/env python3
"""
Kong Gateway Configuration Script
This script configures Kong with services, routes, and plugins
"""

import requests
import time
import json
import sys

KONG_ADMIN_URL = "http://kong:8001"
ORCHESTRATOR_URL = "http://orchestrator:5000"

def wait_for_kong(max_retries=30):
    """Wait for Kong to be ready"""
    print("Waiting for Kong to be ready...")
    for i in range(max_retries):
        try:
            response = requests.get(f"{KONG_ADMIN_URL}/status", timeout=5)
            if response.status_code == 200:
                print("Kong is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"Retry {i+1}/{max_retries}...")
        time.sleep(2)
    return False

def create_service():
    """Create Kong service for orchestrator"""
    print("\nCreating Kong service...")
    
    # Check if service already exists
    try:
        response = requests.get(f"{KONG_ADMIN_URL}/services/orchestrator-service")
        if response.status_code == 200:
            print("Service already exists, updating...")
            response = requests.patch(
                f"{KONG_ADMIN_URL}/services/orchestrator-service",
                json={
                    "url": f"{ORCHESTRATOR_URL}/process-request"
                }
            )
        else:
            response = requests.post(
                f"{KONG_ADMIN_URL}/services",
                json={
                    "name": "orchestrator-service",
                    "url": f"{ORCHESTRATOR_URL}/process-request"
                }
            )
    except:
        response = requests.post(
            f"{KONG_ADMIN_URL}/services",
            json={
                "name": "orchestrator-service",
                "url": f"{ORCHESTRATOR_URL}/process-request"
            }
        )
    
    if response.status_code in [200, 201]:
        print(f"Service created/updated successfully: {response.json()['id']}")
        return response.json()
    else:
        print(f"Failed to create service: {response.text}")
        return None

def create_route(service_id):
    """Create route for the service"""
    print("\nCreating Kong route...")
    
    response = requests.post(
        f"{KONG_ADMIN_URL}/services/{service_id}/routes",
        json={
            "name": "process-request-route",
            "paths": ["/process-request"],
            "methods": ["POST"],
            "strip_path": False
        }
    )
    
    if response.status_code in [200, 201, 409]:
        route = response.json()
        print(f"Route created successfully: {route.get('id', 'existing')}")
        return route
    else:
        print(f"Failed to create route: {response.text}")
        return None

def create_consumer():
    """Create a consumer for API key authentication"""
    print("\nCreating Kong consumer...")
    
    response = requests.post(
        f"{KONG_ADMIN_URL}/consumers",
        json={
            "username": "api-client"
        }
    )
    
    if response.status_code in [200, 201, 409]:
        consumer = response.json()
        print(f"Consumer created: {consumer.get('id', 'existing')}")
        return consumer
    else:
        print(f"Failed to create consumer: {response.text}")
        return None

def create_api_key(consumer_username):
    """Create API key for consumer"""
    print("\nCreating API key...")
    
    response = requests.post(
        f"{KONG_ADMIN_URL}/consumers/{consumer_username}/key-auth",
        json={
            "key": "my-secret-api-key-12345"
        }
    )
    
    if response.status_code in [200, 201, 409]:
        api_key = response.json()
        print(f"API Key created: {api_key.get('key', 'existing')}")
        return api_key
    else:
        print(f"Failed to create API key: {response.text}")
        return None

def enable_key_auth_plugin(service_name):
    """Enable key authentication plugin"""
    print("\nEnabling Key Auth plugin...")
    
    response = requests.post(
        f"{KONG_ADMIN_URL}/services/{service_name}/plugins",
        json={
            "name": "key-auth",
            "config": {
                "key_names": ["X-API-KEY", "apikey"]
            }
        }
    )
    
    if response.status_code in [200, 201, 409]:
        print("Key Auth plugin enabled")
        return response.json()
    else:
        print(f"Failed to enable Key Auth plugin: {response.text}")
        return None

def enable_rate_limiting_plugin(service_name):
    """Enable rate limiting plugin - 5 requests per minute"""
    print("\nEnabling Rate Limiting plugin...")
    
    response = requests.post(
        f"{KONG_ADMIN_URL}/services/{service_name}/plugins",
        json={
            "name": "rate-limiting",
            "config": {
                "minute": 5,
                "policy": "local"
            }
        }
    )
    
    if response.status_code in [200, 201, 409]:
        print("Rate Limiting plugin enabled (5 req/min)")
        return response.json()
    else:
        print(f"Failed to enable Rate Limiting plugin: {response.text}")
        return None

def enable_request_logging():
    """Enable request logging"""
    print("\nEnabling Request Logging...")
    
    response = requests.post(
        f"{KONG_ADMIN_URL}/plugins",
        json={
            "name": "file-log",
            "config": {
                "path": "/logs/kong-requests.log"
            }
        }
    )
    
    if response.status_code in [200, 201, 409]:
        print("Request logging enabled")
        return response.json()
    else:
        print(f"Failed to enable logging: {response.text}")
        return None

def main():
    """Main configuration flow"""
    print("=" * 60)
    print("Kong Gateway Configuration Script")
    print("=" * 60)
    
    # Wait for Kong to be ready
    if not wait_for_kong():
        print("ERROR: Kong did not become ready in time!")
        sys.exit(1)
    
    # Create service
    service = create_service()
    if not service:
        sys.exit(1)
    
    # Create route
    route = create_route("orchestrator-service")
    if not route:
        sys.exit(1)
    
    # Create consumer
    consumer = create_consumer()
    if not consumer:
        sys.exit(1)
    
    # Create API key
    api_key = create_api_key("api-client")
    
    # Enable plugins
    enable_key_auth_plugin("orchestrator-service")
    enable_rate_limiting_plugin("orchestrator-service")
    enable_request_logging()
    
    print("\n" + "=" * 60)
    print("Kong Configuration Complete!")
    print("=" * 60)
    print("\nConfiguration Summary:")
    print(f"  Gateway URL: http://localhost:8000")
    print(f"  Admin API URL: http://localhost:8001")
    print(f"  API Key: my-secret-api-key-12345")
    print(f"  Rate Limit: 5 requests/minute")
    print("\nTest with:")
    print('  curl -X POST http://localhost:8000/process-request \\')
    print('    -H "X-API-KEY: my-secret-api-key-12345" \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"request_id": "req-001", "query": "machine learning"}\'')
    print("=" * 60)

if __name__ == "__main__":
    main()

