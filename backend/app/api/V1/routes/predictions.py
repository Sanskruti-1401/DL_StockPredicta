"""
Prediction Routes
Real-time AI predictions and sentiment analysis endpoints.
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ....db.base import get_db
from ....db.models import Stock, PriceHistory
from ....services.ml_prediction import ml_engine
from ....services.sentiment import sentiment_analyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predictions", tags=["ML Predictions"])


@router.get("/{stock_id}")
async def get_prediction(
    stock_id: int,
    hours_ahead: int = Query(24, ge=1, le=168),  # Max 1 week
    db: Session = Depends(get_db),
):
    """
    Get AI price prediction for a stock.

    Args:
        stock_id: Stock database ID
        hours_ahead: Hours to predict (1-168)

    Returns:
        Prediction with confidence intervals and technical analysis
    """
    try:
        # Get stock
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            return {"error": "Stock not found", "status": 404}

        # Get recent price history
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=30)
        prices = (
            db.query(PriceHistory)
            .filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.date >= cutoff_date,
            )
            .order_by(PriceHistory.date.asc())
            .all()
        )

        if not prices:
            logger.warning(f"⚠️ [Predictions] No price data for stock {stock_id}")
            return {"error": "No price data available", "status": 404}

        # Extract data
        historical_prices = [float(p.close_price) for p in prices]
        historical_dates = [p.date for p in prices]

        # Generate prediction using ML engine
        prediction = ml_engine.predict_price(
            historical_prices=historical_prices,
            historical_dates=historical_dates,
            stock_symbol=stock.symbol,
            prediction_hours=hours_ahead,
        )

        return {
            "status": "success",
            "stock_id": stock_id,
            "stock_symbol": stock.symbol,
            "stock_name": stock.name,
            **prediction,
        }

    except Exception as e:
        logger.error(f"❌ [Predictions] Error for stock {stock_id}: {e}")
        return {
            "error": str(e),
            "status": 500,
        }


@router.get("/batch/all")
async def get_all_predictions(
    hours_ahead: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """
    Get predictions for all active stocks.

    Returns:
        List of predictions for each stock
    """
    try:
        from datetime import datetime, timedelta

        # Get all active stocks
        stocks = db.query(Stock).filter(Stock.active == True).all()

        predictions = []
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        for stock in stocks:
            try:
                prices = (
                    db.query(PriceHistory)
                    .filter(
                        PriceHistory.stock_id == stock.id,
                        PriceHistory.date >= cutoff_date,
                    )
                    .order_by(PriceHistory.date.asc())
                    .all()
                )

                if len(prices) < 2:
                    continue

                historical_prices = [float(p.close_price) for p in prices]
                historical_dates = [p.date for p in prices]

                prediction = ml_engine.predict_price(
                    historical_prices=historical_prices,
                    historical_dates=historical_dates,
                    stock_symbol=stock.symbol,
                    prediction_hours=hours_ahead,
                )

                if prediction.get("status") == "success":
                    predictions.append(
                        {
                            "stock_id": stock.id,
                            "stock_symbol": stock.symbol,
                            "stock_name": stock.name,
                            **prediction,
                        }
                    )
            except Exception as e:
                logger.error(f"❌ Error predicting {stock.symbol}: {e}")
                continue

        logger.info(f"✅ Generated predictions for {len(predictions)}/{len(stocks)} stocks")

        return {
            "status": "success",
            "total_stocks": len(stocks),
            "predicted_stocks": len(predictions),
            "predictions": predictions,
        }

    except Exception as e:
        logger.error(f"❌ [Batch Predictions] Error: {e}")
        return {
            "error": str(e),
            "status": 500,
        }
