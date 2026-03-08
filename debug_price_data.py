#!/usr/bin/env python3
"""
Debug script to verify stock price data is available and correctly formatted.
Run this with: python debug_price_data.py
"""

import sys
import requests
from datetime import datetime, timedelta

# Backend base URL
BASE_URL = "http://localhost:8000/api/v1"

def check_backend():
    """Check if backend is running."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✓ Backend is running (status {response.status_code})")
        return True
    except Exception as e:
        print(f"✗ Backend not responding: {e}")
        print("  Start backend with: cd backend && python -m uvicorn app.main:app --reload")
        return False

def get_stocks():
    """Get list of all stocks."""
    try:
        response = requests.get(f"{BASE_URL}/stocks?limit=20")
        if response.status_code == 200:
            stocks = response.json()
            print(f"✓ Found {len(stocks)} stocks")
            return stocks
        else:
            print(f"✗ Error getting stocks: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Error getting stocks: {e}")
        return []

def check_price_history(stock_id, symbol, days=7):
    """Check price history for a stock."""
    try:
        url = f"{BASE_URL}/stocks/{stock_id}/price-history?days={days}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data or len(data) == 0:
                print(f"  - {symbol}: No price data in database!")
                return False
            
            print(f"  - {symbol}: {len(data)} price records")
            
            # Show first and last record
            first = data[0]
            last = data[-1]
            
            print(f"      First: {first['date']} close={first.get('close', 'N/A')}")
            print(f"      Last:  {last['date']} close={last.get('close', 'N/A')}")
            
            # Verify required fields
            required_fields = ['date', 'open', 'high', 'low', 'close']
            for record in [first, last]:
                for field in required_fields:
                    if field not in record:
                        print(f"      ✗ Missing field '{field}' in response!")
                        return False
            
            return True
        else:
            print(f"  - {symbol}: Error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  - {symbol}: Exception: {e}")
        return False

def main():
    print("=" * 60)
    print("Stock Predictor - Price Data Diagnostic")
    print("=" * 60)
    print()
    
    # Check backend
    if not check_backend():
        sys.exit(1)
    print()
    
    # Get stocks
    print("Checking stocks...")
    stocks = get_stocks()
    if not stocks:
        sys.exit(1)
    print()
    
    # Check price history for each stock
    print("Checking price history for each stock (last 7 days)...")
    all_good = True
    for stock in stocks[:5]:  # Just check first 5 to keep output manageable
        if not check_price_history(stock['id'], stock['symbol']):
            all_good = False
    print()
    
    # Summary
    print("=" * 60)
    if all_good:
        print("✓ All checks passed! Price data is available.")
        print()
        print("If prices still don't display in sidebar:")
        print("1. Open browser DevTools (F12)")
        print("2. Go to Network tab")
        print("3. Refresh the page")
        print("4. Look for /price-history requests")
        print("5. Check the response data format")
        print("6. Check Console tab for JavaScript errors")
    else:
        print("✗ Issues detected. Check output above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
