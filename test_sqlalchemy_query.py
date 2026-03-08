#!/usr/bin/env python3
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.models import Stock
from app.core.config import settings

# Create an engine with fresh connection
print(f"Using database: {settings.DATABASE_URL}")

# Create engine with fresh session
engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Query stock using SQLAlchemy ORM
db: Session = SessionLocal()
try:
    stock = db.query(Stock).filter(Stock.symbol == "AAPL").first()
    if stock:
        print(f"Stock: {stock.symbol}")
        print(f"Market Cap: {stock.market_cap}")
        print(f"Dividend Yield: {stock.dividend_yield}")
        print(f"PE Ratio: {stock.pe_ratio}")
    else:
        print("Stock not found")
finally:
    db.close()
