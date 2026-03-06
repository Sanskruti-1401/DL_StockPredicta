"""
Market data fetching and management service.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from ..db.models import Stock, PriceHistory
from ..core.config import settings

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for fetching and managing market data."""

    def __init__(self, db: Session):
        self.db = db
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.polygon_key = settings.POLYGON_API_KEY

    def fetch_price_history(self, symbol: str, days: int = 365) -> List[dict]:
        """
        Fetch historical price data for a stock.
        
        Args:
            symbol: Stock symbol
            days: Number of days of history to fetch
            
        Returns:
            List of price data dictionaries
        """
        try:
            # This would integrate with real APIs (Alpha Vantage, Polygon, etc.)
            # For now, returning sample structure
            logger.info(f"Fetching price history for {symbol} ({days} days)")
            
            # In production, call external API here
            # return self._fetch_from_alpha_vantage(symbol, days)
            
            return []
        except Exception as e:
            logger.error(f"Error fetching price history for {symbol}: {e}")
            return []

    def update_price_data(self, stock_id: int, price_data: dict) -> Optional[PriceHistory]:
        """
        Store or update price data in database.
        
        Args:
            stock_id: Stock ID
            price_data: Price data dictionary
            
        Returns:
            Created/updated PriceHistory record
        """
        try:
            # Check if price data already exists for this date
            existing = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.date == price_data['date']
            ).first()
            
            if existing:
                # Update existing record
                for key, value in price_data.items():
                    if key != 'date':
                        setattr(existing, key, value)
            else:
                # Create new record
                existing = PriceHistory(
                    stock_id=stock_id,
                    date=price_data['date'],
                    open_price=price_data.get('open', 0.0),
                    high_price=price_data.get('high', 0.0),
                    low_price=price_data.get('low', 0.0),
                    close_price=price_data.get('close', 0.0),
                    volume=price_data.get('volume'),
                    adjusted_close=price_data.get('adjusted_close'),
                )
                self.db.add(existing)
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating price data: {e}")
            return None

    def get_latest_price(self, stock_id: int) -> Optional[float]:
        """Get the latest closing price for a stock."""
        try:
            latest = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id
            ).order_by(PriceHistory.date.desc()).first()
            
            return latest.close_price if latest else None
        except Exception as e:
            logger.error(f"Error getting latest price: {e}")
            return None

    def get_price_range(self, stock_id: int, days: int = 365) -> dict:
        """Get price range statistics for a stock."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            prices = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.date >= cutoff_date
            ).order_by(PriceHistory.date.asc()).all()
            
            if not prices:
                return {}
            
            closing_prices = [p.close_price for p in prices]
            
            return {
                "high_52_week": max(closing_prices),
                "low_52_week": min(closing_prices),
                "average_price": sum(closing_prices) / len(closing_prices),
                "current_price": closing_prices[-1],
            }
        except Exception as e:
            logger.error(f"Error getting price range: {e}")
            return {}

    def sync_market_data(self, symbols: List[str]) -> dict:
        """
        Sync market data for a list of stocks.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Sync statistics
        """
        stats = {
            "total": len(symbols),
            "synced": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            for symbol in symbols:
                try:
                    # Fetch stock
                    stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
                    if not stock:
                        stats["failed"] += 1
                        stats["errors"].append(f"Stock {symbol} not found")
                        continue
                    
                    # Fetch and update price history
                    price_data = self.fetch_price_history(symbol)
                    for data in price_data:
                        self.update_price_data(stock.id, data)
                    
                    stats["synced"] += 1
                    logger.info(f"Successfully synced {symbol}")
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append(f"Error syncing {symbol}: {str(e)}")
                    logger.error(f"Error syncing {symbol}: {e}")
            
            return stats
        except Exception as e:
            logger.error(f"Error in sync_market_data: {e}")
            return stats

    def calculate_returns(self, stock_id: int, period: str = "1M") -> Optional[float]:
        """
        Calculate stock returns for a period.
        
        Args:
            stock_id: Stock ID
            period: Period (1M, 3M, 6M, 1Y)
            
        Returns:
            Return percentage
        """
        try:
            period_days = {
                "1M": 30,
                "3M": 90,
                "6M": 180,
                "1Y": 365,
            }.get(period, 30)
            
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            current = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id
            ).order_by(PriceHistory.date.desc()).first()
            
            past = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.date <= cutoff_date
            ).order_by(PriceHistory.date.desc()).first()
            
            if current and past:
                return_pct = ((current.close_price - past.close_price) / past.close_price) * 100
                return float(return_pct)
            
            return None
        except Exception as e:
            logger.error(f"Error calculating returns: {e}")
            return None

    def _fetch_from_alpha_vantage(self, symbol: str, days: int) -> List[dict]:
        """Fetch data from Alpha Vantage API."""
        # Implementation would use requests library
        # https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={key}
        pass

    def _fetch_from_polygon(self, symbol: str, days: int) -> List[dict]:
        """Fetch data from Polygon.io API."""
        # Implementation would use requests library
        # https://api.polygon.io/v1/open-close/{symbol}/{date}
        pass
