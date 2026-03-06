"""
News sentiment analysis service.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from ..db.models import Stock, NewsArticle
from ..core.config import settings

logger = logging.getLogger(__name__)


class NewsSentimentService:
    """Service for fetching and analyzing news sentiment."""

    def __init__(self, db: Session):
        self.db = db
        self.newsapi_key = settings.NEWSAPI_API_KEY

    def fetch_news(self, symbol: str, limit: int = 50) -> List[dict]:
        """
        Fetch latest news for a stock.
        
        Args:
            symbol: Stock symbol
            limit: Number of articles to fetch
            
        Returns:
            List of news articles
        """
        try:
            logger.info(f"Fetching news for {symbol}")
            
            # Integration with NewsAPI
            # https://newsapi.org/v2/everything?q={symbol}&sortBy=publishedAt&language=en
            
            # Mock implementation for now
            return []
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    def analyze_sentiment(self, text: str) -> tuple[str, float]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (sentiment, score)
        """
        try:
            # Base implementation - would use TextBlob, VADER, or transformer models
            # For production, consider using:
            # - TextBlob (simple)
            # - VADER (financial tweets)
            # - FinBERT (fine-tuned for finance)
            # - GPT models (advanced)
            
            from textblob import TextBlob
            
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            
            if polarity > 0.1:
                sentiment = "POSITIVE"
            elif polarity < -0.1:
                sentiment = "NEGATIVE"
            else:
                sentiment = "NEUTRAL"
            
            return sentiment, float(polarity)
        except ImportError:
            # TextBlob not installed, use simple heuristic
            logger.warning("TextBlob not installed, using simple sentiment analysis")
            return self._simple_sentiment(text)
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return "NEUTRAL", 0.0

    def process_news(self, stock_id: int, articles: List[dict]) -> List[NewsArticle]:
        """
        Process and store news articles with sentiment analysis.
        
        Args:
            stock_id: Stock ID
            articles: List of article dictionaries
            
        Returns:
            List of stored NewsArticle records
        """
        stored_articles = []
        
        try:
            for article in articles:
                # Check if article already exists
                existing = self.db.query(NewsArticle).filter(
                    NewsArticle.url == article.get('url')
                ).first()
                
                if existing:
                    continue
                
                # Analyze sentiment
                text = f"{article.get('title', '')} {article.get('description', '')}"
                sentiment, score = self.analyze_sentiment(text)
                
                # Create article record
                news_article = NewsArticle(
                    stock_id=stock_id,
                    title=article.get('title', ''),
                    description=article.get('description'),
                    source=article.get('source', {}).get('name') if isinstance(article.get('source'), dict) else article.get('source'),
                    url=article.get('url'),
                    sentiment=sentiment,
                    sentiment_score=score,
                    confidence=abs(score),
                    published_date=self._parse_date(article.get('publishedAt')),
                    fetched_at=datetime.utcnow(),
                )
                
                self.db.add(news_article)
                stored_articles.append(news_article)
            
            self.db.commit()
            logger.info(f"Processed {len(stored_articles)} news articles for stock {stock_id}")
            return stored_articles
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing news: {e}")
            return stored_articles

    def get_sentiment_summary(self, stock_id: int, days: int = 7) -> dict:
        """
        Get sentiment summary for a stock.
        
        Args:
            stock_id: Stock ID
            days: Number of days to analyze
            
        Returns:
            Sentiment summary statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            articles = self.db.query(NewsArticle).filter(
                NewsArticle.stock_id == stock_id,
                NewsArticle.fetched_at >= cutoff_date
            ).all()
            
            if not articles:
                return {
                    "total_articles": 0,
                    "average_sentiment": 0.0,
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0,
                    "sentiment_trend": "NEUTRAL",
                }
            
            sentiment_scores = [a.sentiment_score for a in articles if a.sentiment_score]
            positive_count = sum(1 for a in articles if a.sentiment == "POSITIVE")
            negative_count = sum(1 for a in articles if a.sentiment == "NEGATIVE")
            neutral_count = sum(1 for a in articles if a.sentiment == "NEUTRAL")
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            
            # Determine trend
            if avg_sentiment > 0.1:
                trend = "POSITIVE"
            elif avg_sentiment < -0.1:
                trend = "NEGATIVE"
            else:
                trend = "NEUTRAL"
            
            return {
                "total_articles": len(articles),
                "average_sentiment": float(avg_sentiment),
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "sentiment_trend": trend,
                "positive_percent": (positive_count / len(articles)) * 100 if articles else 0,
                "negative_percent": (negative_count / len(articles)) * 100 if articles else 0,
            }
        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            return {}

    def get_latest_sentiment(self, stock_id: int) -> Optional[float]:
        """Get the latest sentiment score for a stock."""
        try:
            latest = self.db.query(NewsArticle).filter(
                NewsArticle.stock_id == stock_id
            ).order_by(NewsArticle.fetched_at.desc()).first()
            
            return latest.sentiment_score if latest else None
        except Exception as e:
            logger.error(f"Error getting latest sentiment: {e}")
            return None

    def fetch_and_process_news(self, stock_id: int, symbol: str) -> dict:
        """
        Fetch and process news for a stock.
        
        Args:
            stock_id: Stock ID
            symbol: Stock symbol
            
        Returns:
            Processing statistics
        """
        try:
            # Fetch news
            articles = self.fetch_news(symbol)
            
            # Process articles
            processed = self.process_news(stock_id, articles)
            
            # Get summary
            summary = self.get_sentiment_summary(stock_id)
            
            return {
                "articles_fetched": len(articles),
                "articles_processed": len(processed),
                "sentiment_summary": summary,
            }
        except Exception as e:
            logger.error(f"Error fetching and processing news: {e}")
            return {"error": str(e)}

    def _simple_sentiment(self, text: str) -> tuple[str, float]:
        """Simple sentiment analysis without external libraries."""
        positive_words = ["good", "great", "excellent", "strong", "growth", "gain", "profit", "bullish", "up"]
        negative_words = ["bad", "poor", "weak", "loss", "decline", "drop", "bearish", "down", "risk", "concern"]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "POSITIVE"
            score = min((positive_count - negative_count) / 10, 1.0)
        elif negative_count > positive_count:
            sentiment = "NEGATIVE"
            score = -min((negative_count - positive_count) / 10, 1.0)
        else:
            sentiment = "NEUTRAL"
            score = 0.0
        
        return sentiment, score

    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_string:
            return None
        
        try:
            # Handle ISO 8601 format
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            return None

    def sync_news(self, symbols: List[str]) -> dict:
        """
        Sync news for multiple stocks.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Sync statistics
        """
        stats = {
            "total": len(symbols),
            "synced": 0,
            "failed": 0,
            "total_articles": 0,
        }
        
        try:
            for symbol in symbols:
                try:
                    stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
                    if not stock:
                        stats["failed"] += 1
                        continue
                    
                    result = self.fetch_and_process_news(stock.id, symbol)
                    if "error" not in result:
                        stats["synced"] += 1
                        stats["total_articles"] += result.get("articles_processed", 0)
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Error syncing news for {symbol}: {e}")
            
            return stats
        except Exception as e:
            logger.error(f"Error in sync_news: {e}")
            return stats
