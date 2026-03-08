"""
Sentiment Analysis Routes
Stock sentiment endpoints for news and market sentiment.
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from ....db.base import get_db
from ....db.models import Stock
from ....services.sentiment import sentiment_analyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])


class NewsArticle(BaseModel):
    """News article for sentiment analysis."""

    title: str
    content: Optional[str] = None


@router.get("/{stock_id}")
async def get_stock_sentiment(
    stock_id: int,
    db: Session = Depends(get_db),
):
    """
    Get sentiment analysis for a stock.

    Returns:
        Sentiment metrics (overall score from -1 to 1)
    """
    try:
        # Get stock
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            return {"error": "Stock not found", "status": 404}

        # Get sentiment (using mock for now, can integrate real news API)
        sentiment = sentiment_analyzer.get_sentiment_for_stock(stock.symbol)

        return {
            "status": "success",
            "stock_id": stock_id,
            "stock_symbol": stock.symbol,
            "stock_name": stock.name,
            **sentiment,
        }

    except Exception as e:
        logger.error(f"❌ [Sentiment] Error for stock {stock_id}: {e}")
        return {
            "error": str(e),
            "status": 500,
        }


@router.post("/{stock_id}/analyze")
async def analyze_sentiment(
    stock_id: int,
    articles: List[NewsArticle],
    db: Session = Depends(get_db),
):
    """
    Analyze sentiment for custom articles about a stock.

    Args:
        stock_id: Stock database ID
        articles: List of articles to analyze

    Returns:
        Aggregated sentiment analysis
    """
    try:
        # Get stock
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            return {"error": "Stock not found", "status": 404}

        # Convert articles to dict format
        article_dicts = [a.dict() for a in articles]

        # Analyze
        sentiment = sentiment_analyzer.analyze_articles(article_dicts)

        return {
            "status": "success",
            "stock_id": stock_id,
            "stock_symbol": stock.symbol,
            **sentiment,
        }

    except Exception as e:
        logger.error(f"❌ [Sentiment] Analysis error for stock {stock_id}: {e}")
        return {
            "error": str(e),
            "status": 500,
        }


@router.get("/batch/all")
async def get_all_sentiment(db: Session = Depends(get_db)):
    """
    Get sentiment for all active stocks.

    Returns:
        List of sentiment analyses for each stock
    """
    try:
        # Get all active stocks
        stocks = db.query(Stock).filter(Stock.active == True).all()

        sentiment_data = []
        for stock in stocks:
            try:
                sentiment = sentiment_analyzer.get_sentiment_for_stock(stock.symbol)
                sentiment_data.append(
                    {
                        "stock_id": stock.id,
                        "stock_symbol": stock.symbol,
                        **sentiment,
                    }
                )
            except Exception as e:
                logger.error(f"❌ Error analyzing sentiment for {stock.symbol}: {e}")
                continue

        logger.info(f"✅ Generated sentiment for {len(sentiment_data)}/{len(stocks)} stocks")

        return {
            "status": "success",
            "total_stocks": len(stocks),
            "analyzed_stocks": len(sentiment_data),
            "sentiment_data": sentiment_data,
        }

    except Exception as e:
        logger.error(f"❌ [Batch Sentiment] Error: {e}")
        return {
            "error": str(e),
            "status": 500,
        }
