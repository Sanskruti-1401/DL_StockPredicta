import requests
import json

response = requests.get("http://localhost:8000/api/v1/stocks?limit=1")
data = response.json()

print("API Response:")
print(json.dumps(data, indent=2))

if data:
    stock = data[0]
    print(f"\nFields:")
    print(f"  market_cap: {stock.get('market_cap')}")
    print(f"  dividend_yield: {stock.get('dividend_yield')}")
    print(f"  pe_ratio: {stock.get('pe_ratio')}")
    
    print(f"\nAll keys in response:")
    for key in stock.keys():
        print(f"  {key}: {stock[key]}")
