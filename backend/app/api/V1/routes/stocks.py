"""
Stock management routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....db.base import get_db
from ....db.models import Stock, User
from ..schemas.stock import StockSchema, StockDetailSchema, StockCreateSchema, StockUpdateSchema
from ....services.market_data import MarketDataService
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("", response_model=list[StockSchema])
async def list_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sector: str | None = None,
    db: Session = Depends(get_db)
):
    """List all stocks with optional filtering."""
    try:
        query = db.query(Stock)
        
        if sector:
            query = query.filter(Stock.sector == sector)
        
        stocks = query.offset(skip).limit(limit).all()
        return stocks
    except Exception as e:
        logger.error(f"Error listing stocks: {e}")
        raise HTTPException(status_code=500, detail="Error listing stocks")


@router.get("/search", response_model=list[StockSchema])
async def search_stocks(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search stocks by symbol or name."""
    try:
        stocks = db.query(Stock).filter(
            (Stock.symbol.ilike(f"%{q}%")) |
            (Stock.name.ilike(f"%{q}%"))
        ).limit(limit).all()
        
        return stocks
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        raise HTTPException(status_code=500, detail="Error searching stocks")


@router.get("/{stock_id}", response_model=StockDetailSchema)
async def get_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    market_data_service: MarketDataService = Depends(lambda db=Depends(get_db): MarketDataService(db))
):
    """Get detailed information about a stock."""
    try:
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        # Get current price
        current_price = market_data_service.get_latest_price(stock_id)
        
        if not current_price:
            raise HTTPException(status_code=404, detail="No price data available")
        
        # Get price range
        price_range = market_data_service.get_price_range(stock_id)
        
        # Prepare response (would include latest prediction and news)
        return {
            **stock.__dict__,
            "current_price": current_price,
            "price_change": 0.0,  # Calculate from previous close
            "price_change_percent": 0.0,
            "fifty_two_week_high": price_range.get("high_52_week", 0.0),
            "fifty_two_week_low": price_range.get("low_52_week", 0.0),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock: {e}")
        raise HTTPException(status_code=500, detail="Error getting stock")


@router.post("", response_model=StockSchema)
async def create_stock(
    stock_data: StockCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new stock (admin only)."""
    try:
        # Check if stock already exists
        existing = db.query(Stock).filter(Stock.symbol == stock_data.symbol).first()
        if existing:
            raise HTTPException(status_code=400, detail="Stock already exists")
        
        stock = Stock(**stock_data.dict())
        db.add(stock)
        db.commit()
        db.refresh(stock)
        
        logger.info(f"Stock created: {stock.symbol}")
        return stock
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating stock: {e}")
        raise HTTPException(status_code=500, detail="Error creating stock")


@router.put("/{stock_id}", response_model=StockSchema)
async def update_stock(
    stock_id: int,
    stock_data: StockUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update stock information."""
    try:
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        # Update only provided fields
        update_data = stock_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(stock, key, value)
        
        db.commit()
        db.refresh(stock)
        
        logger.info(f"Stock updated: {stock.symbol}")
        return stock
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating stock: {e}")
        raise HTTPException(status_code=500, detail="Error updating stock")


@router.delete("/{stock_id}")
async def delete_stock(
    stock_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a stock (admin only)."""
    try:
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        db.delete(stock)
        db.commit()
        
        logger.info(f"Stock deleted: {stock.symbol}")
        return {"message": "Stock deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting stock: {e}")
        raise HTTPException(status_code=500, detail="Error deleting stock")


@router.get("/{stock_id}/sectors", response_model=list[dict])
async def get_sectors(db: Session = Depends(get_db)):
    """Get all unique sectors."""
    try:
        sectors = db.query(Stock.sector).distinct().filter(Stock.sector.isnot(None)).all()
        return [{"sector": s[0]} for s in sectors]
    except Exception as e:
        logger.error(f"Error getting sectors: {e}")
        raise HTTPException(status_code=500, detail="Error getting sectors")


@router.get("/{stock_id}/price-history")
async def get_price_history(
    stock_id: int,
    days: int = Query(365, ge=1, le=1825),  # Max 5 years
    db: Session = Depends(get_db)
):
    """Get price history for a stock."""
    try:
        from datetime import datetime, timedelta
        from ...db.models import PriceHistory
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        prices = db.query(PriceHistory).filter(
            PriceHistory.stock_id == stock_id,
            PriceHistory.date >= cutoff_date
        ).order_by(PriceHistory.date.asc()).all()
        
        if not prices:
            raise HTTPException(status_code=404, detail="No price history found")
        
        return [
            {
                "date": p.date,
                "open": p.open_price,
                "high": p.high_price,
                "low": p.low_price,
                "close": p.close_price,
                "volume": p.volume,
            }
            for p in prices
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price history: {e}")
        raise HTTPException(status_code=500, detail="Error getting price history")
