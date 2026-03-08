"""
Sentiment Analysis Service
Analyzes news sentiment and market sentiment for stocks.
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Sentiment analysis for stock-related news and social media.
    Uses lexicon-based sentiment scoring with fallback to simple keyword matching.
    """

    def __init__(self):
        # Positive and negative sentiment keywords
        self.positive_words = {
            "bullish", "growth", "surge", "rally", "boom", "soar", "gain", "profit",
            "excellent", "strong", "outperform", "beat", "upgrade", "buy", "positive",
            "rise", "up", "bull", "momentum", "strength", "recovery", "rally",
        }

        self.negative_words = {
            "bearish", "decline", "crash", "drop", "plunge", "loss", "poor", "weak",
            "downgrade", "sell", "negative", "fall", "down", "bear", "weakness",
            "concern", "warning", "risk", "debt", "layoff", "miss", "loss",
        }

        self.intensifiers = {"very", "extremely", "significantly", "significantly"}
        self.negators = {"not", "no", "never", "unlikely"}

    def analyze_text(self, text: str) -> float:
        """
        Analyze sentiment of text and return score between -1 and 1.

        Args:
            text: Text to analyze (news headline, article, etc.)

        Returns:
            float: Sentiment score (-1 to 1)
        """
        try:
            if not text or len(text.strip()) < 3:
                return 0.0

            # Normalize text
            text_lower = text.lower()
            words = re.findall(r'\w+', text_lower)

            if not words:
                return 0.0

            # Calculate sentiment
            positive_count = sum(1 for word in words if word in self.positive_words)
            negative_count = sum(1 for word in words if word in self.negative_words)

            # Calculate raw score
            total = positive_count + negative_count
            if total == 0:
                return 0.0  # Neutral

            raw_score = (positive_count - negative_count) / total

            # Apply intensity weighting
            has_intensifier = any(word in words for word in self.intensifiers)
            if has_intensifier:
                raw_score *= 1.3

            # Clip to [-1, 1] range
            sentiment_score = max(-1.0, min(1.0, raw_score))

            logger.debug(f"📊 [Sentiment] Text: '{text[:100]}' → Score: {sentiment_score:.2f}")
            return sentiment_score

        except Exception as e:
            logger.error(f"❌ [Sentiment] Analysis error: {e}")
            return 0.0

    def analyze_articles(self, articles: List[Dict]) -> Dict:
        """
        Analyze multiple articles and calculate aggregate sentiment.

        Args:
            articles: List of article dicts with 'title' and/or 'content' fields

        Returns:
            Dict with sentiment metrics
        """
        if not articles:
            return self._neutral_sentiment_response()

        try:
            scores = []
            for article in articles:
                text = f"{article.get('title', '')} {article.get('content', '')}"
                score = self.analyze_text(text)
                scores.append(score)

            avg_score = sum(scores) / len(scores) if scores else 0.0
            positive_count = sum(1 for s in scores if s > 0.2)
            negative_count = sum(1 for s in scores if s < -0.2)

            sentiment_label = self._get_sentiment_label(avg_score)

            logger.info(
                f"[Sentiment] Analyzed {len(articles)} articles: "
                f"Avg={avg_score:.2f}, Positive={positive_count}, Negative={negative_count}"
            )

            return {
                "status": "success",
                "overall_sentiment": round(float(avg_score), 2),
                "sentiment_label": sentiment_label,
                "positive_articles": positive_count,
                "negative_articles": negative_count,
                "neutral_articles": len(articles) - positive_count - negative_count,
                "total_articles": len(articles),
                "individual_scores": [round(s, 2) for s in scores],
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ [Sentiment] Article analysis error: {e}")
            return self._neutral_sentiment_response()

    def get_sentiment_for_stock(
        self, stock_symbol: str, recent_news: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Get sentiment analysis for a stock.

        Args:
            stock_symbol: Stock ticker symbol
            recent_news: Recent news articles (optional)

        Returns:
            Dict with sentiment data
        """
        if recent_news:
            return self.analyze_articles(recent_news)
        else:
            # Return mock sentiment based on stock (seeded variation)
            return self._generate_mock_sentiment(stock_symbol)

    def _get_sentiment_label(self, score: float) -> str:
        """Convert numerical sentiment score to label."""
        if score >= 0.6:
            return "Very Bullish"
        elif score >= 0.2:
            return "Bullish"
        elif score > -0.2:
            return "Neutral"
        elif score >= -0.6:
            return "Bearish"
        else:
            return "Very Bearish"

    def _generate_mock_sentiment(self, stock_symbol: str) -> Dict:
        """Generate realistic mock sentiment for demonstration."""
        # Seed sentiment based on stock symbol
        seed = hash(stock_symbol) % 100
        base_sentiment = (seed - 50) / 100  # Range: -0.5 to 0.5

        label = self._get_sentiment_label(base_sentiment)

        # Vary article counts based on seed for realistic variation
        total_articles = 8 + (seed % 15)  # Range: 8-22 articles
        
        # Distribute based on sentiment
        if base_sentiment > 0.2:
            # Positive sentiment: more positive articles
            positive_articles = int(total_articles * (0.5 + base_sentiment))
            negative_articles = int(total_articles * (0.2 - (base_sentiment * 0.1)))
        elif base_sentiment < -0.2:
            # Negative sentiment: more negative articles
            negative_articles = int(total_articles * (0.5 + abs(base_sentiment)))
            positive_articles = int(total_articles * (0.2 - (abs(base_sentiment) * 0.1)))
        else:
            # Neutral sentiment: balanced
            positive_articles = int(total_articles * 0.35)
            negative_articles = int(total_articles * 0.35)
        
        neutral_articles = total_articles - positive_articles - negative_articles
        
        # Ensure non-negative counts
        positive_articles = max(0, positive_articles)
        negative_articles = max(0, negative_articles)
        neutral_articles = max(0, neutral_articles)

        return {
            "status": "success",
            "stock_symbol": stock_symbol,
            "overall_sentiment": round(base_sentiment, 2),
            "sentiment_label": label,
            "positive_articles": positive_articles,
            "negative_articles": negative_articles,
            "neutral_articles": neutral_articles,
            "total_articles": positive_articles + negative_articles + neutral_articles,
            "source": "mock",
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def _neutral_sentiment_response(self) -> Dict:
        """Return neutral sentiment response."""
        return {
            "status": "success",
            "overall_sentiment": 0.0,
            "sentiment_label": "Neutral",
            "positive_articles": 0,
            "negative_articles": 0,
            "neutral_articles": 0,
            "analyzed_at": datetime.utcnow().isoformat(),
        }


# Global instance
sentiment_analyzer = SentimentAnalyzer()
