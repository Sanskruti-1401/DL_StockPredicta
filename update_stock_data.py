#!/usr/bin/env python3
"""
Update stocks with market cap and dividend yield data.
This script updates all stocks in the database with real values from SEED_STOCKS.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Stock
from app.core.config import settings

# Stock seed data with market cap and dividend yield
SEED_STOCKS = [
    {"symbol": "AAPL", "market_cap": 3000000000000, "dividend_yield": 0.44},
    {"symbol": "MSFT", "market_cap": 2800000000000, "dividend_yield": 0.73},
    {"symbol": "GOOGL", "market_cap": 1800000000000, "dividend_yield": 0.0},
    {"symbol": "AMZN", "market_cap": 1700000000000, "dividend_yield": 0.0},
    {"symbol": "NVDA", "market_cap": 1100000000000, "dividend_yield": 0.03},
    {"symbol": "META", "market_cap": 600000000000, "dividend_yield": 0.0},
    {"symbol": "TSLA", "market_cap": 800000000000, "dividend_yield": 0.0},
    {"symbol": "JPM", "market_cap": 500000000000, "dividend_yield": 2.19},
    {"symbol": "JNJ", "market_cap": 420000000000, "dividend_yield": 2.65},
    {"symbol": "V", "market_cap": 570000000000, "dividend_yield": 0.69},
]

def update_stocks():
    """Update stocks with market cap and dividend yield."""
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        updated = 0
        failed = 0
        
        for stock_data in SEED_STOCKS:
            try:
                stock = db.query(Stock).filter(Stock.symbol == stock_data["symbol"]).first()
                
                if stock:
                    stock.market_cap = stock_data["market_cap"]
                    stock.dividend_yield = stock_data["dividend_yield"]
                    db.commit()
                    print(f"✅ Updated {stock_data['symbol']}: Market Cap=${stock_data['market_cap']/1e9:.1f}B, Yield={stock_data['dividend_yield']*100:.2f}%")
                    updated += 1
                else:
                    print(f"⚠️  Stock {stock_data['symbol']} not found in database")
                    failed += 1
            except Exception as e:
                db.rollback()
                print(f"❌ Error updating {stock_data['symbol']}: {e}")
                failed += 1
        
        db.close()
        print(f"\n Summary: {updated} updated, {failed} failed")
        return updated, failed
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return 0, len(SEED_STOCKS)

if __name__ == "__main__":
    print("Updating stocks with market cap and dividend yield data...\n")
    updated, failed = update_stocks()
    sys.exit(0 if failed == 0 else 1)
