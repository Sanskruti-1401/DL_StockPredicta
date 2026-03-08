#!/usr/bin/env python3
"""
Test all API endpoints to diagnose issues.
Run with: python test_api_endpoints.py
"""

import requests
import json
from typing import Any, Dict

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(method: str, endpoint: str, name: str) -> Dict[str, Any]:
    """Test an API endpoint and return results."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, timeout=5)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"Response Body:")
            print(json.dumps(data, indent=2))
            return {"success": True, "status": response.status_code, "data": data}
        except json.JSONDecodeError:
            print(f"Response: {response.text[:200]}")
            return {"success": False, "status": response.status_code, "error": "Invalid JSON"}
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("Backend may not be running!")
        return {"success": False, "error": "Connection refused"}
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: Request took too long")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

def main():
    print("\n" + "="*70)
    print("STOCK PREDICTOR - API ENDPOINT DIAGNOSTICS")
    print("="*70)
    
    # Test 1: Health check
    health = test_endpoint("GET", "/health", "Health Check")
    
    if not health.get("success"):
        print("\n" + "!"*70)
        print("❌ BACKEND NOT RESPONDING")
        print("Start backend with: cd backend && python -m uvicorn app.main:app --reload")
        print("!"*70)
        return
    
    # Test 2: List stocks
    stocks = test_endpoint("GET", "/stocks?limit=20", "List Stocks")
    
    if stocks.get("success"):
        stock_count = len(stocks.get("data", []))
        print(f"\n✅ Found {stock_count} stocks")
        
        if stock_count > 0:
            first_stock_id = stocks["data"][0].get("id", 1)
            
            # Test 3: Get predictions
            test_endpoint("GET", f"/predictions/{first_stock_id}?hours_ahead=24", f"Predictions for Stock {first_stock_id}")
            
            # Test 4: Get sentiment
            test_endpoint("GET", f"/sentiment/{first_stock_id}", f"Sentiment for Stock {first_stock_id}")
            
            # Test 5: Get price history
            test_endpoint("GET", f"/stocks/{first_stock_id}/price-history?days=7", f"Price History for Stock {first_stock_id}")
    
    print("\n" + "="*70)
    print("DIAGNOSTICS COMPLETE")
    print("="*70)
    print("\nIf predictions/sentiment are returning errors:")
    print("1. Check backend logs for error messages")
    print("2. Verify database has price data: python test_recommendation.py")
    print("3. Check if background tasks are running")
    print("="*70)

if __name__ == "__main__":
    main()
