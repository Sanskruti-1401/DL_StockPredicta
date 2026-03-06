"""
Stock prediction service using ML models and technical/sentiment analysis.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pickle
import numpy as np
from sqlalchemy.orm import Session

from ..db.models import Stock, StockPrediction, TechnicalIndicator, NewsArticle, PriceHistory
from ..api.V1.schemas.prediction import PredictionSchema, PredictionCreateSchema

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for generating stock price predictions and recommendations."""

    def __init__(self, db: Session):
        self.db = db
        self.price_model = None
        self.recommendation_model = None
        self.scaler = None

    def load_models(self, price_model_path: str, recommendation_model_path: str, scaler_path: str):
        """Load ML models from disk."""
        try:
            with open(price_model_path, 'rb') as f:
                self.price_model = pickle.load(f)
            with open(recommendation_model_path, 'rb') as f:
                self.recommendation_model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info("Models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

    def get_latest_prediction(self, stock_id: int) -> Optional[StockPrediction]:
        """Get the latest prediction for a stock."""
        return self.db.query(StockPrediction).filter(
            StockPrediction.stock_id == stock_id
        ).order_by(StockPrediction.created_at.desc()).first()

    def predict_price(self, stock_id: int, days_ahead: int = 30) -> Tuple[float, float]:
        """
        Predict future stock price.
        
        Args:
            stock_id: Stock ID
            days_ahead: Number of days to predict ahead
            
        Returns:
            Tuple of (predicted_price, confidence_score)
        """
        try:
            # Get historical price data
            price_data = self._get_features(stock_id)
            
            if self.price_model is None or not price_data:
                logger.warning(f"Cannot predict: model not loaded or no price data for stock {stock_id}")
                return None, None

            # Scale features
            scaled_features = self.scaler.transform([price_data])
            
            # Make prediction
            predicted_price = self.price_model.predict(scaled_features)[0]
            
            # Get confidence (some models provide this)
            confidence = getattr(self.price_model, '_predict_proba', lambda x: [0.85])(scaled_features)[0]
            
            return float(predicted_price), float(confidence)
        except Exception as e:
            logger.error(f"Error in price prediction: {e}")
            return None, None

    def recommend_action(self, stock_id: int, predicted_price: float, current_price: float) -> Tuple[str, float, str]:
        """
        Generate buy/sell/hold recommendation.
        
        Args:
            stock_id: Stock ID
            predicted_price: Model-predicted future price
            current_price: Current stock price
            
        Returns:
            Tuple of (recommendation, confidence, reason)
        """
        try:
            # Calculate price movement
            price_change_percent = ((predicted_price - current_price) / current_price) * 100
            
            # Get technical and sentiment scores
            technical_score = self._get_technical_score(stock_id)
            sentiment_score = self._get_sentiment_score(stock_id)
            
            # Combine signals
            combined_score = (
                (price_change_percent / 100 * 0.4) +  # 40% weight on price prediction
                (technical_score * 0.35) +  # 35% weight on technical indicators
                (sentiment_score * 0.25)    # 25% weight on sentiment
            )
            
            # Determine recommendation
            if combined_score > 0.15:
                recommendation = "BUY"
                reason = f"Predicted upside of {price_change_percent:.2f}%, positive technical signals and news sentiment"
            elif combined_score < -0.15:
                recommendation = "SELL"
                reason = f"Predicted downside of {abs(price_change_percent):.2f}%, negative technical signals and news sentiment"
            else:
                recommendation = "HOLD"
                reason = "Mixed signals, wait for clearer direction"
            
            confidence = min(abs(combined_score) + 0.5, 1.0)
            
            return recommendation, confidence, reason
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "HOLD", 0.5, "Unable to generate recommendation"

    def get_technical_indicators(self, stock_id: int) -> dict:
        """Get latest technical indicators for a stock."""
        try:
            latest_indicator = self.db.query(TechnicalIndicator).filter(
                TechnicalIndicator.stock_id == stock_id
            ).order_by(TechnicalIndicator.date.desc()).first()
            
            if not latest_indicator:
                return {}
            
            return {
                "rsi": latest_indicator.rsi,
                "macd": latest_indicator.macd,
                "bollinger_bands_signal": "UPPER" if latest_indicator.bb_upper else "MIDDLE" if latest_indicator.bb_middle else "LOWER",
                "moving_average_50": latest_indicator.sma_50,
                "moving_average_200": latest_indicator.sma_200,
                "volatility": latest_indicator.volatility,
            }
        except Exception as e:
            logger.error(f"Error getting technical indicators: {e}")
            return {}

    def create_prediction(self, stock_id: int, data: PredictionCreateSchema) -> StockPrediction:
        """Create and store a new prediction."""
        try:
            prediction = StockPrediction(
                stock_id=stock_id,
                predicted_price=data.predicted_price,
                price_confidence=data.price_confidence,
                predicted_volatility=data.predicted_volatility,
                price_change_percent=data.price_change_percent,
                recommendation=data.recommendation,
                recommendation_confidence=data.recommendation_confidence,
                recommendation_reason=data.recommendation_reason,
                rsi=data.rsi,
                macd=data.macd,
                bollinger_bands_signal=data.bollinger_bands_signal,
                moving_average_50=data.moving_average_50,
                moving_average_200=data.moving_average_200,
                news_sentiment_score=data.news_sentiment_score,
                sentiment_impact=data.sentiment_impact,
                market_correlation=data.market_correlation,
                index_influence=data.index_influence,
                model_version=data.model_version,
            )
            self.db.add(prediction)
            self.db.commit()
            self.db.refresh(prediction)
            logger.info(f"Prediction created for stock {stock_id}")
            return prediction
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating prediction: {e}")
            raise

    def get_prediction_accuracy(self, stock_id: int, days: int = 30) -> float:
        """
        Calculate prediction accuracy for a stock.
        
        Args:
            stock_id: Stock ID
            days: Number of days to analyze
            
        Returns:
            Accuracy score 0-1
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            predictions = self.db.query(StockPrediction).filter(
                StockPrediction.stock_id == stock_id,
                StockPrediction.created_at >= cutoff_date
            ).all()
            
            if not predictions:
                return 0.0
            
            # Calculate accuracy based on whether predictions matched actual movement
            accuracy_scores = []
            for pred in predictions:
                # Get actual price after prediction
                actual_price_data = self.db.query(PriceHistory).filter(
                    PriceHistory.stock_id == stock_id,
                    PriceHistory.date > pred.created_at
                ).order_by(PriceHistory.date.asc()).first()
                
                if actual_price_data:
                    predicted_direction = "UP" if pred.price_change_percent > 0 else "DOWN"
                    actual_direction = "UP" if actual_price_data.close_price > pred.predicted_price else "DOWN"
                    
                    if predicted_direction == actual_direction:
                        accuracy_scores.append(pred.price_confidence or 0.5)
            
            return sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
        except Exception as e:
            logger.error(f"Error calculating prediction accuracy: {e}")
            return 0.0

    def _get_features(self, stock_id: int) -> list:
        """Extract features for model prediction."""
        try:
            # Get last 100 days of price data
            price_history = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id
            ).order_by(PriceHistory.date.desc()).limit(100).all()
            
            if not price_history:
                return []
            
            # Calculate features
            prices = [p.close_price for p in reversed(price_history)]
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns)
            mean_return = np.mean(returns)
            
            features = [
                prices[-1],  # Current price
                volatility,  # Volatility
                mean_return,  # Average return
                np.max(prices) - np.min(prices),  # Price range
                prices[-1] - prices[0],  # Price change
            ]
            
            return features
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return []

    def _get_technical_score(self, stock_id: int) -> float:
        """Calculate technical indicator score -1 to 1."""
        try:
            indicators = self.db.query(TechnicalIndicator).filter(
                TechnicalIndicator.stock_id == stock_id
            ).order_by(TechnicalIndicator.date.desc()).first()
            
            if not indicators:
                return 0.0
            
            score = 0.0
            
            # RSI signal (30-70 range is neutral)
            if indicators.rsi:
                if indicators.rsi < 30:
                    score += 0.4  # Oversold = bullish
                elif indicators.rsi > 70:
                    score -= 0.4  # Overbought = bearish
            
            # MACD signal
            if indicators.macd and indicators.macd_signal:
                if indicators.macd > indicators.macd_signal:
                    score += 0.3  # Bullish crossover
                else:
                    score -= 0.3  # Bearish crossover
            
            # Moving average signal
            if indicators.sma_50 and indicators.sma_200:
                if indicators.sma_50 > indicators.sma_200:
                    score += 0.3  # Bullish trend
                else:
                    score -= 0.3  # Bearish trend
            
            return np.clip(score, -1.0, 1.0)
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return 0.0

    def _get_sentiment_score(self, stock_id: int) -> float:
        """Calculate sentiment score from news -1 to 1."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            articles = self.db.query(NewsArticle).filter(
                NewsArticle.stock_id == stock_id,
                NewsArticle.fetched_at >= cutoff_date
            ).all()
            
            if not articles:
                return 0.0
            
            sentiment_scores = [a.sentiment_score for a in articles if a.sentiment_score]
            
            if not sentiment_scores:
                return 0.0
            
            return np.mean(sentiment_scores)
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.0
