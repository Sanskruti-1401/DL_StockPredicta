import requests

response = requests.get('http://localhost:8000/api/v1/stocks?limit=1')
stock = response.json()[0]

print('✅ FIXED! API now returns complete stock data:')
print(f'  Symbol: {stock["symbol"]}')
if stock["market_cap"]:
    print(f'  Market Cap: ${stock["market_cap"] / 1e9:.2f}B')
else:
    print('  Market Cap: N/A')
    
if stock["dividend_yield"]:
    print(f'  Dividend Yield: {stock["dividend_yield"] * 100:.2f}%')
else:
    print('  Dividend Yield: N/A')
    
print(f'  P/E Ratio: {stock["pe_ratio"]}')
print(f'  Sector: {stock["sector"]}')
