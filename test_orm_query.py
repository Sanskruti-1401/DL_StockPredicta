import sys
sys.path.insert(0, '/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.models import Stock
from backend.app.core.config import settings

print(f"Using DATABASE_URL: {settings.DATABASE_URL}")

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Query using ORM
stock = session.query(Stock).first()
print(f"\nORM Query Result:")
print(f"  symbol: {stock.symbol}")
print(f"  market_cap: {stock.market_cap}")
print(f"  dividend_yield: {stock.dividend_yield}")
print(f"  pe_ratio: {stock.pe_ratio}")

# Check what columns SQLAlchemy loaded
print(f"\nStock.__dict__:")
for key, value in stock.__dict__.items():
    if not key.startswith('_') and value is not None:
        print(f"  {key}: {value}")

session.close()
