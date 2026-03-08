"""
WebSocket routes for real-time market data streaming.
"""
import logging
import asyncio
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from sqlalchemy.orm import Session

from ....db.base import get_db
from ....db.models import Stock, PriceHistory
from ....services.ml_prediction import ml_engine
from ....services.sentiment import sentiment_analyzer

logger = logging.getLogger(__name__)
router = APIRouter()

# Active WebSocket connections per stock
active_connections: dict[int, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections for real-time data."""
    
    def __init__(self):
        self.active_connections: dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, stock_id: int):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        if stock_id not in self.active_connections:
            self.active_connections[stock_id] = set()
        self.active_connections[stock_id].add(websocket)
        logger.debug(f"WebSocket client connected to stock {stock_id} ({len(self.active_connections[stock_id])} total)")
    
    def disconnect(self, stock_id: int, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if stock_id in self.active_connections:
            self.active_connections[stock_id].discard(websocket)
            if not self.active_connections[stock_id]:
                del self.active_connections[stock_id]
            logger.debug(f"WebSocket client disconnected from stock {stock_id}")
    
    async def broadcast_to_stock(self, stock_id: int, data: dict):
        """Broadcast data to all clients connected to a stock."""
        if stock_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[stock_id]:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(stock_id, connection)


manager = ConnectionManager()


@router.websocket("/ws/market-data/{stock_id}")
async def websocket_market_data(websocket: WebSocket, stock_id: int, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time market data.
    
    Streams:
    - Real-time price updates
    - AI predictions
    - Sentiment analysis
    
    Every 30 seconds, new data is sent to connected clients.
    """
    # Verify stock exists
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        await websocket.close(code=4004, reason="Stock not found")
        return
    
    await manager.connect(websocket, stock_id)
    
    try:
        while True:
            try:
                # Get latest price
                latest_price = db.query(PriceHistory).filter(
                    PriceHistory.stock_id == stock_id
                ).order_by(PriceHistory.date.desc()).first()
                
                # Get 30-day historical for prediction
                price_history = db.query(PriceHistory).filter(
                    PriceHistory.stock_id == stock_id
                ).order_by(PriceHistory.date.desc()).limit(30).all()
                
                if latest_price and len(price_history) >= 10:
                    prices = [float(ph.close) for ph in reversed(price_history)]
                    
                    # Generate prediction
                    prediction = ml_engine.predict_price(prices)
                    
                    # Get sentiment
                    sentiment = sentiment_analyzer.get_sentiment_for_stock(stock.symbol)
                    
                    # Prepare real-time data
                    realtime_data = {
                        "timestamp": latest_price.date.isoformat(),
                        "stock_id": stock_id,
                        "symbol": stock.symbol,
                        "current_price": float(latest_price.close),
                        "price_change": float(latest_price.close) - float(latest_price.open),
                        "prediction": prediction,
                        "sentiment": sentiment,
                    }
                    
                    # Send to client
                    await websocket.send_json(realtime_data)
                    logger.debug(f"📡 Sent real-time data for {stock.symbol}")
                
                # Wait 30 seconds before next update
                await asyncio.sleep(30)
                
            except WebSocketDisconnect:
                manager.disconnect(stock_id, websocket)
                return
            except Exception as e:
                logger.error(f"WebSocket error for stock {stock_id}: {e}")
                try:
                    await websocket.send_json({"error": str(e)})
                except:
                    pass
                await asyncio.sleep(5)  # Brief delay before retry
    
    finally:
        manager.disconnect(stock_id, websocket)


@router.websocket("/ws/market-data/batch/all")
async def websocket_batch_market_data(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time market data for ALL stocks.
    
    Streams data for all 10 stocks every 30 seconds.
    """
    await websocket.accept()
    logger.debug("WebSocket batch client connected (all stocks)")
    
    try:
        while True:
            try:
                stocks = db.query(Stock).all()
                batch_data = []
                
                for stock in stocks:
                    try:
                        latest_price = db.query(PriceHistory).filter(
                            PriceHistory.stock_id == stock.id
                        ).order_by(PriceHistory.date.desc()).first()
                        
                        price_history = db.query(PriceHistory).filter(
                            PriceHistory.stock_id == stock.id
                        ).order_by(PriceHistory.date.desc()).limit(30).all()
                        
                        if latest_price and len(price_history) >= 10:
                            prices = [float(ph.close) for ph in reversed(price_history)]
                            prediction = ml_engine.predict_price(prices)
                            sentiment = sentiment_analyzer.get_sentiment_for_stock(stock.symbol)
                            
                            batch_data.append({
                                "stock_id": stock.id,
                                "symbol": stock.symbol,
                                "current_price": float(latest_price.close),
                                "prediction_recommendation": prediction["recommendation"],
                                "sentiment_label": sentiment["sentiment_label"],
                            })
                    except Exception as e:
                        logger.error(f"Error processing {stock.symbol} in batch: {e}")
                
                # Send batch to client
                await websocket.send_json({
                    "timestamp": asyncio.get_event_loop().time(),
                    "stocks": batch_data,
                })
                logger.debug("📡 Sent batch real-time data for all stocks")
                
                # Wait 30 seconds before next update
                await asyncio.sleep(30)
                
            except WebSocketDisconnect:
                logger.debug("WebSocket batch client disconnected")
                return
            except Exception as e:
                logger.error(f"Batch WebSocket error: {e}")
                try:
                    await websocket.send_json({"error": str(e)})
                except:
                    pass
                await asyncio.sleep(5)
    
    finally:
        logger.debug("WebSocket batch connection closed")
