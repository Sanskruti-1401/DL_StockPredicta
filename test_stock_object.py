import sys
sys.path.insert(0, '/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.models import Stock

# Create a session with the test database
engine = create_engine("sqlite:///test.db")
Session = sessionmaker(bind=engine)
session = Session()

# Query a stock
stock = session.query(Stock).first()

print("Stock object attributes:")
print(f"  id: {stock.id}")
print(f"  symbol: {stock.symbol}")
print(f"  name: {stock.name}")
print(f"  sector: {stock.sector}")
print(f"  market_cap: {stock.market_cap}")
print(f"  dividend_yield: {stock.dividend_yield}")
print(f"  pe_ratio: {stock.pe_ratio}")
print(f"  beta: {stock.beta}")

print("\nStock __dict__:")
for key, value in stock.__dict__.items():
    if not key.startswith('_'):
        print(f"  {key}: {value}")

session.close()
