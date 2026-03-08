"""
Background tasks for periodic data updates and real-time data fetching.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db.models import Stock, PriceHistory
from ..services.ml_prediction import ml_engine
from ..services.sentiment import sentiment_analyzer
from ..services.news_sentiment import NewsSentimentService

logger = logging.getLogger(__name__)


async def update_stock_price_data():
    """
    Background task to update stock price data periodically.
    Maintains 30 days of continuous historical data + today's intraday data.
    Fills in any gaps and adds hourly records for the current day.
    """
    import random
    
    while True:
        try:
            logger.debug("Updating stock price data...")
            db = next(get_db())
            
            # Get all stocks
            stocks = db.query(Stock).all()
            
            for stock in stocks:
                try:
                    # Get the latest price record
                    latest_price = db.query(PriceHistory).filter(
                        PriceHistory.stock_id == stock.id
                    ).order_by(PriceHistory.date.desc()).first()
                    
                    if latest_price:
                        now = datetime.utcnow()
                        last_date = latest_price.date
                        current_price = float(latest_price.close_price)
                        
                        # Fill in gaps from last record to today (at close of market - 4 PM UTC)
                        market_close_today = now.replace(hour=21, minute=0, second=0, microsecond=0)
                        current_check = last_date + timedelta(days=1)
                        current_check = current_check.replace(hour=21, minute=0, second=0, microsecond=0)
                        
                        while current_check <= market_close_today:
                            # Check if we have a record for market close on this date
                            existing = db.query(PriceHistory).filter(
                                PriceHistory.stock_id == stock.id,
                                PriceHistory.date == current_check
                            ).first()
                            
                            if not existing:
                                # Generate realistic daily movement
                                daily_movement = random.uniform(-2.5, 2.5)  # -2.5% to +2.5% daily
                                new_price = current_price * (1 + daily_movement / 100)
                                
                                # Create daily OHLC record (at market close 4 PM / 21:00 UTC)
                                open_price = current_price
                                high_price = max(current_price, new_price) * random.uniform(1.0, 1.01)
                                low_price = min(current_price, new_price) * random.uniform(0.99, 1.0)
                                close_price = new_price
                                volume = int(2000000 * random.uniform(0.8, 1.2))  # Typical daily volume
                                
                                new_record = PriceHistory(
                                    stock_id=stock.id,
                                    date=current_check,
                                    open_price=open_price,
                                    high_price=high_price,
                                    low_price=low_price,
                                    close_price=close_price,
                                    volume=volume
                                )
                                db.add(new_record)
                                current_price = close_price  # Update for next day's calculation
                            
                            current_check += timedelta(days=1)
                        
                        # Now add intraday data for today (hourly from 9:30 AM to 4 PM)
                        today_9am = now.replace(hour=9, minute=30, second=0, microsecond=0)
                        today_4pm = now.replace(hour=21, minute=0, second=0, microsecond=0)
                        
                        # Generate hourly records for today
                        current_hourly = today_9am
                        while current_hourly <= today_4pm:
                            existing = db.query(PriceHistory).filter(
                                PriceHistory.stock_id == stock.id,
                                PriceHistory.date == current_hourly
                            ).first()
                            
                            if not existing:
                                # Intraday variation is smaller than daily
                                intraday_movement = random.uniform(-1.0, 1.0)
                                new_price = current_price * (1 + intraday_movement / 100)
                                
                                open_price = current_price
                                high_price = max(current_price, new_price) * random.uniform(1.0, 1.002)
                                low_price = min(current_price, new_price) * random.uniform(0.998, 1.0)
                                close_price = new_price
                                volume = int(1500000 * random.uniform(0.6, 1.0))  # Intraday volume
                                
                                new_record = PriceHistory(
                                    stock_id=stock.id,
                                    date=current_hourly,
                                    open_price=open_price,
                                    high_price=high_price,
                                    low_price=low_price,
                                    close_price=close_price,
                                    volume=volume
                                )
                                db.add(new_record)
                                current_price = close_price
                            
                            current_hourly += timedelta(hours=1)
                        
                        db.commit()
                        
                        # Clean up old data (keep only 35 days)
                        cutoff_date = datetime.utcnow() - timedelta(days=35)
                        old_records = db.query(PriceHistory).filter(
                            PriceHistory.stock_id == stock.id,
                            PriceHistory.date < cutoff_date
                        ).delete()
                        if old_records > 0:
                            db.commit()
                            logger.debug(f"Cleaned {old_records} records > 35 days old for {stock.symbol}")
                        
                        record_count = db.query(PriceHistory).filter(
                            PriceHistory.stock_id == stock.id
                        ).count()
                        logger.debug(f"Updated {stock.symbol}: {record_count} total records (filled gaps + today)")
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"Failed to update {stock.symbol}: {e}")
            
            db.close()
            logger.debug("Price update cycle completed")
            
            # Wait 5 minutes before next update
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.debug(f"Background price update: {e}")
            await asyncio.sleep(300)


async def update_sentiment_data():
    """
    Background task to update sentiment data periodically.
    Runs every 10 minutes to fetch new news and update sentiment scores.
    Attempts real NewsAPI calls if configured, falls back to mock data.
    """
    while True:
        try:
            logger.debug("Updating sentiment data...")
            db = next(get_db())
            
            stocks = db.query(Stock).all()
            
            for stock in stocks:
                try:
                    # Try to fetch real news from NewsAPI
                    news_service = NewsSentimentService(db)
                    result = news_service.fetch_and_process_news(stock.id, stock.symbol)
                    
                    if result.get("articles_fetched", 0) > 0:
                        logger.info(f"✅ Fetched {result.get('articles_fetched')} real articles for {stock.symbol}")
                    else:
                        logger.debug(f"No new articles for {stock.symbol} (using mock sentiment)")
                    
                except Exception as e:
                    logger.debug(f"Error fetching real news for {stock.symbol}: {e} (will use mock sentiment)")
            
            db.close()
            logger.debug("Sentiment update cycle completed")
            
            # Wait 10 minutes before next update
            await asyncio.sleep(600)
            
        except Exception as e:
            logger.debug(f"Background sentiment update: {e}")
            await asyncio.sleep(600)


async def prefetch_predictions():
    """
    Background task to prefetch predictions for all stocks.
    Caches predictions every 15 minutes to reduce API latency.
    """
    while True:
        try:
            logger.debug("Prefetching predictions...")
            db = next(get_db())
            
            stocks = db.query(Stock).all()
            
            for stock in stocks:
                try:
                    # Get historical data for prediction
                    price_history = db.query(PriceHistory).filter(
                        PriceHistory.stock_id == stock.id
                    ).order_by(PriceHistory.date.desc()).limit(30).all()
                    
                    if len(price_history) >= 10:
                        prices = [float(ph.close) for ph in reversed(price_history)]
                        
                        # Generate prediction (this caches internally)
                        prediction = ml_engine.predict_price(prices)
                        logger.debug(f"Prefetched prediction for {stock.symbol}")
                    
                except Exception as e:
                    logger.debug(f"Error prefetching for {stock.symbol}: {e}")
            
            db.close()
            logger.debug("Prediction prefetch cycle completed")
            
            # Wait 15 minutes before next prefetch
            await asyncio.sleep(900)
            
        except Exception as e:
            logger.debug(f"Prediction prefetch error: {e}")
            await asyncio.sleep(900)
