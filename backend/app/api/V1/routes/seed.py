"""
Data seeding routes for initial stock population.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import random

from ....db.base import get_db
from ....db.models import Stock, PriceHistory
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/seed", tags=["Data Seeding"])

# ==================== 10-Stock Seed List ====================
# Popular US stocks across different sectors for initial data population

SEED_STOCKS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 3000000000000,  # ~3 trillion
        "pe_ratio": 28.5,
        "dividend_yield": 0.44,
        "beta": 1.16,
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software",
        "market_cap": 2800000000000,
        "pe_ratio": 35.2,
        "dividend_yield": 0.73,
        "beta": 0.90,
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "sector": "Technology",
        "industry": "Internet Services",
        "market_cap": 1800000000000,
        "pe_ratio": 26.5,
        "dividend_yield": 0.0,
        "beta": 1.08,
    },
    {
        "symbol": "AMZN",
        "name": "Amazon.com Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Internet Retail",
        "market_cap": 1700000000000,
        "pe_ratio": 58.3,
        "dividend_yield": 0.0,
        "beta": 1.18,
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "sector": "Technology",
        "industry": "Semiconductors",
        "market_cap": 1100000000000,
        "pe_ratio": 65.5,
        "dividend_yield": 0.03,
        "beta": 1.73,
    },
    {
        "symbol": "META",
        "name": "Meta Platforms Inc.",
        "sector": "Technology",
        "industry": "Internet Services",
        "market_cap": 600000000000,
        "pe_ratio": 24.2,
        "dividend_yield": 0.0,
        "beta": 1.26,
    },
    {
        "symbol": "TSLA",
        "name": "Tesla Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Automotive",
        "market_cap": 800000000000,
        "pe_ratio": 68.5,
        "dividend_yield": 0.0,
        "beta": 2.40,
    },
    {
        "symbol": "JPM",
        "name": "JPMorgan Chase & Co.",
        "sector": "Financial",
        "industry": "Banking",
        "market_cap": 500000000000,
        "pe_ratio": 13.5,
        "dividend_yield": 2.19,
        "beta": 1.10,
    },
    {
        "symbol": "JNJ",
        "name": "Johnson & Johnson",
        "sector": "Healthcare",
        "industry": "Pharmaceuticals",
        "market_cap": 420000000000,
        "pe_ratio": 23.8,
        "dividend_yield": 2.65,
        "beta": 0.60,
    },
    {
        "symbol": "V",
        "name": "Visa Inc.",
        "sector": "Financial",
        "industry": "Payment Processing",
        "market_cap": 570000000000,
        "pe_ratio": 46.5,
        "dividend_yield": 0.69,
        "beta": 1.04,
    },
]


class SeedResponse(BaseModel):
    """Response model for seeding operations."""
    created: int
    skipped: int
    failed: int
    message: str


class StockSeedList(BaseModel):
    """10-stock seed list information."""
    total: int
    stocks: List[dict]
    description: str


# ==================== Helper Functions ====================

def generate_price_history(stock_id: int, symbol: str, days: int = 90):
    """
    Generate synthetic historical price data for a stock.
    
    Args:
        stock_id: Database stock ID
        symbol: Stock symbol (for realistic price ranges)
        days: Number of days to generate (default 90 for better technical analysis)
    
    Returns:
        List of PriceHistory objects
    """
    # Base prices for realistic ranges
    base_prices = {
        "AAPL": 190, "MSFT": 430, "GOOGL": 150, "AMZN": 180, "NVDA": 875,
        "META": 525, "TSLA": 240, "JPM": 200, "JNJ": 160, "V": 290
    }
    
    base_price = base_prices.get(symbol, 100)
    volatility = random.uniform(0.01, 0.04)  # 1-4% daily volatility
    
    prices = []
    current_price = base_price
    
    # Generate daily prices for the last 'days' days
    for i in range(days, 0, -1):
        # Random walk with trend
        daily_return = random.gauss(0.0005, volatility)  # Mean return + random movement
        current_price = current_price * (1 + daily_return)
        
        # Add realistic OHLC variations
        open_price = current_price
        high_price = open_price * (1 + random.uniform(0, 0.02))
        low_price = open_price * (1 - random.uniform(0, 0.02))
        close_price = random.uniform(low_price, high_price)
        volume = random.randint(1000000, 100000000)
        
        # Use market close time (4 PM = 21:00 UTC)
        date = (datetime.utcnow() - timedelta(days=i)).replace(hour=21, minute=0, second=0, microsecond=0)
        
        price_record = PriceHistory(
            stock_id=stock_id,
            date=date,
            open_price=round(open_price, 2),
            high_price=round(high_price, 2),
            low_price=round(low_price, 2),
            close_price=round(close_price, 2),
            volume=volume,
            adjusted_close=round(close_price, 2)
        )
        prices.append(price_record)
        current_price = close_price
    
    # Generate hourly data for today (9:30 AM to 4 PM UTC)
    today = datetime.utcnow()
    today_9am = today.replace(hour=9, minute=30, second=0, microsecond=0)
    today_4pm = today.replace(hour=21, minute=0, second=0, microsecond=0)
    
    current_intraday = today_9am
    intraday_price = current_price
    
    while current_intraday <= today_4pm:
        # Smaller intraday volatility
        intraday_return = random.gauss(0.00001, volatility / 10)
        intraday_price = intraday_price * (1 + intraday_return)
        
        hour_record = PriceHistory(
            stock_id=stock_id,
            date=current_intraday,
            open_price=round(intraday_price * 0.99, 2),
            high_price=round(intraday_price * 1.01, 2),
            low_price=round(intraday_price * 0.99, 2),
            close_price=round(intraday_price, 2),
            volume=random.randint(500000, 10000000),
            adjusted_close=round(intraday_price, 2)
        )
        prices.append(hour_record)
        current_intraday += timedelta(hours=1)
    
    return prices


# ==================== Seed Endpoints ====================

@router.post("/stocks", response_model=SeedResponse)
async def seed_initial_stocks(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Seed the database with initial 10 popular US stocks.
    
    **10-Stock List**:
    - AAPL, MSFT, GOOGL, AMZN (Big Tech)
    - NVDA (Semiconductors)
    - META (Social Media)
    - TSLA (Electric Vehicles)
    - JPM, V (Finance)
    - JNJ (Healthcare)
    
    **Data Included**:
    - Symbol, Name
    - Sector, Industry
    - Market Cap, P/E Ratio
    - Dividend Yield, Beta
    
    Only creates stocks that don't already exist (checks symbol).
    """
    try:
        created = 0
        skipped = 0
        failed = 0
        
        logger.info(f"Starting seed with {len(SEED_STOCKS)} stocks")
        
        for stock_data in SEED_STOCKS:
            try:
                # Check if stock already exists
                existing = db.query(Stock).filter(
                    Stock.symbol == stock_data["symbol"]
                ).first()
                
                if existing:
                    logger.info(f"Stock {stock_data['symbol']} already exists, skipping")
                    skipped += 1
                    continue
                
                # Create new stock
                stock = Stock(**stock_data)
                db.add(stock)
                db.commit()
                
                logger.info(f"Created stock: {stock_data['symbol']}")
                created += 1
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error creating {stock_data['symbol']}: {e}")
                failed += 1
        
        return SeedResponse(
            created=created,
            skipped=skipped,
            failed=failed,
            message=f"Seed completed: {created} created, {skipped} skipped, {failed} failed"
        )
        
    except Exception as e:
        logger.error(f"Error in seed operation: {e}")
        raise HTTPException(status_code=500, detail=f"Seed error: {str(e)}")


@router.get("/stocks/list", response_model=StockSeedList)
async def get_seed_list():
    """
    Get the 10-stock seed list information.
    
    Useful for understanding what stocks will be seeded and their characteristics.
    """
    return StockSeedList(
        total=len(SEED_STOCKS),
        stocks=SEED_STOCKS,
        description="10 popular US stocks across technology, finance, healthcare, and consumer sectors"
    )


@router.delete("/stocks")
async def clear_all_stocks(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    WARNING: Delete all stocks from database.
    
    Use with caution - this removes all stocks and their related data.
    """
    try:
        count = db.query(Stock).delete()
        db.commit()
        
        logger.warning(f"Deleted {count} stocks from database")
        
        return {
            "message": f"Deleted {count} stocks",
            "warning": "All associated price history and predictions are also deleted"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing stocks: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
