"""
News and sentiment analysis routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ....db.base import get_db
from ....db.models import Stock, NewsArticle, User
from ....services.news_sentiment import NewsSentimentService
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["News"])


@router.get("/stocks/{stock_id}")
async def get_stock_news(
    stock_id: int,
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=365),
    sentiment: str | None = Query(None, regex="^(POSITIVE|NEGATIVE|NEUTRAL)$"),
    db: Session = Depends(get_db)
):
    """Get news articles for a stock."""
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(NewsArticle).filter(
            NewsArticle.stock_id == stock_id,
            NewsArticle.fetched_at >= cutoff_date
        )
        
        if sentiment:
            query = query.filter(NewsArticle.sentiment == sentiment)
        
        articles = query.order_by(NewsArticle.fetched_at.desc()).limit(limit).all()
        
        return [
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "source": a.source,
                "url": a.url,
                "sentiment": a.sentiment,
                "sentiment_score": a.sentiment_score,
                "confidence": a.confidence,
                "published_date": a.published_date,
                "fetched_at": a.fetched_at,
            }
            for a in articles
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock news: {e}")
        raise HTTPException(status_code=500, detail="Error getting news")


@router.get("/stocks/{stock_id}/sentiment")
async def get_sentiment_analysis(
    stock_id: int,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    news_service: NewsSentimentService = Depends(lambda db=Depends(get_db): NewsSentimentService(db))
):
    """Get sentiment analysis summary for a stock."""
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        summary = news_service.get_sentiment_summary(stock_id, days)
        
        return {
            "stock_symbol": stock.symbol,
            "stock_id": stock_id,
            "analysis_period_days": days,
            **summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail="Error getting sentiment analysis")


@router.post("/stocks/{stock_id}/sync")
async def sync_news(
    stock_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    news_service: NewsSentimentService = Depends(lambda db=Depends(get_db): NewsSentimentService(db))
):
    """Manually sync news for a stock."""
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        result = news_service.fetch_and_process_news(stock_id, stock.symbol)
        
        return {
            "stock_symbol": stock.symbol,
            "stock_id": stock_id,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing news: {e}")
        raise HTTPException(status_code=500, detail="Error syncing news")


@router.get("/sentiment-trending")
async def get_trending_sentiment(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get stocks with trending positive or negative sentiment."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get sentiment averages per stock
        from sqlalchemy import func
        
        results = db.query(
            Stock.id,
            Stock.symbol,
            Stock.name,
            func.avg(NewsArticle.sentiment_score).label("avg_sentiment"),
            func.count(NewsArticle.id).label("article_count")
        ).join(NewsArticle).filter(
            NewsArticle.fetched_at >= cutoff_date
        ).group_by(
            Stock.id, Stock.symbol, Stock.name
        ).order_by(
            func.avg(NewsArticle.sentiment_score).desc()
        ).limit(limit).all()
        
        return [
            {
                "stock_id": r[0],
                "symbol": r[1],
                "name": r[2],
                "average_sentiment": float(r[3]) if r[3] else 0.0,
                "article_count": r[4],
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Error getting trending sentiment: {e}")
        raise HTTPException(status_code=500, detail="Error getting trending sentiment")


@router.get("/sentiment-comparison")
async def compare_sentiment(
    symbols: list[str] = Query(..., min_items=1, max_items=10),
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    news_service: NewsSentimentService = Depends(lambda db=Depends(get_db): NewsSentimentService(db))
):
    """Compare sentiment across multiple stocks."""
    try:
        comparison = []
        
        for symbol in symbols:
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                continue
            
            summary = news_service.get_sentiment_summary(stock.id, days)
            
            comparison.append({
                "symbol": symbol,
                "stock_id": stock.id,
                **summary
            })
        
        return comparison
    except Exception as e:
        logger.error(f"Error comparing sentiment: {e}")
        raise HTTPException(status_code=500, detail="Error comparing sentiment")


@router.get("/stocks/{stock_id}/sentiment-history")
async def get_sentiment_history(
    stock_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get sentiment history for a stock."""
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily sentiment averages
        from sqlalchemy import func
        from sqlalchemy.sql import text
        
        # Group by date
        articles = db.query(
            func.date(NewsArticle.fetched_at).label("date"),
            func.avg(NewsArticle.sentiment_score).label("avg_sentiment"),
            func.count(NewsArticle.id).label("count")
        ).filter(
            NewsArticle.stock_id == stock_id,
            NewsArticle.fetched_at >= cutoff_date
        ).group_by(
            func.date(NewsArticle.fetched_at)
        ).order_by(
            func.date(NewsArticle.fetched_at).desc()
        ).all()
        
        return [
            {
                "date": str(a[0]),
                "average_sentiment": float(a[1]) if a[1] else 0.0,
                "article_count": a[2],
            }
            for a in articles
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentiment history: {e}")
        raise HTTPException(status_code=500, detail="Error getting sentiment history")
