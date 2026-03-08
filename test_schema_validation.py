import sys
sys.path.insert(0, '/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.models import Stock
from backend.app.api.V1.schemas.stock import StockSchema

# Create a session with the test database
engine = create_engine("sqlite:///test.db")
Session = sessionmaker(bind=engine)
session = Session()

# Query a stock
stock = session.query(Stock).first()

print("1. Stock object attributes:")
print(f"  market_cap: {stock.market_cap}")
print(f"  dividend_yield: {stock.dividend_yield}")
print(f"  pe_ratio: {stock.pe_ratio}")

print("\n2. Pydantic schema validation:")
schema = StockSchema.model_validate(stock, from_attributes=True)
print(f"  market_cap: {schema.market_cap}")
print(f"  dividend_yield: {schema.dividend_yield}")
print(f"  pe_ratio: {schema.pe_ratio}")

print("\n3. Schema as dict:")
schema_dict = schema.model_dump()
print(f"  market_cap: {schema_dict.get('market_cap')}")
print(f"  dividend_yield: {schema_dict.get('dividend_yield')}")
print(f"  pe_ratio: {schema_dict.get('pe_ratio')}")

print("\n4. Full schema dict:")
for key, value in schema_dict.items():
    if value is not None and key not in ['id', 'symbol', 'name', 'created_at', 'updated_at']:
        print(f"  {key}: {value}")

session.close()
