"""
ML Prediction Service
Generates AI price predictions using trend analysis and volatility modeling.
"""
import logging
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MLPredictionEngine:
    """Machine Learning prediction engine for stock price forecasting."""

    def __init__(self):
        self.model_version = "1.0.0"
        self.confidence_threshold = 0.6

    def predict_price(
        self,
        historical_prices: List[float],
        historical_dates: List[datetime],
        stock_symbol: str,
        prediction_hours: int = 24,
    ) -> Dict:
        """
        Generate AI price predictions with confidence intervals.

        Args:
            historical_prices: List of historical closing prices
            historical_dates: List of corresponding dates
            stock_symbol: Stock symbol for logging
            prediction_hours: Hours ahead to predict (default 24)

        Returns:
            Dict with predictions, confidence, volatility analysis
        """
        try:
            if len(historical_prices) < 2:
                logger.warning(f"[ML] Insufficient data for {stock_symbol}")
                return self._create_error_response()

            prices = np.array(historical_prices, dtype=float)

            # Calculate technical indicators
            volatility = self._calculate_volatility(prices)
            trend = self._calculate_trend(prices)
            rsi = self._calculate_rsi(prices)
            momentum = self._calculate_momentum(prices)

            # Generate predictions
            current_price = prices[-1]
            predictions = []

            for i in range(1, prediction_hours + 1):
                time_step = i / prediction_hours
                # Confidence decreases as we forecast further
                confidence = max(0.5, 0.95 - time_step * 0.35)

                # Price prediction with trend and volatility
                price_change = trend * (i / 5) + (np.random.randn() * volatility)
                predicted_price = current_price * (1 + price_change / 100)

                # Confidence interval (margin of error)
                margin = volatility * (1 + time_step * 2) / 100

                predictions.append({
                    "hour": i,
                    "timestamp": (datetime.utcnow() + timedelta(hours=i)).isoformat(),
                    "price": round(float(predicted_price), 2),
                    "confidence": round(float(confidence), 2),
                    "upper_bound": round(float(predicted_price * (1 + margin)), 2),
                    "lower_bound": round(float(predicted_price * (1 - margin)), 2),
                })

            # Calculate recommendation
            final_price = predictions[-1]["price"]
            price_change_pct = ((final_price - current_price) / current_price) * 100
            recommendation = self._generate_recommendation(
                price_change_pct, rsi, momentum, confidence
            )

            logger.info(
                f"✅ [ML] Generated predictions for {stock_symbol}: "
                f"Trend={trend:.2f}%, Vol={volatility:.2f}%, RSI={rsi:.1f}, "
                f"Rec={recommendation}"
            )

            return {
                "status": "success",
                "stock_symbol": stock_symbol,
                "current_price": float(current_price),
                "predictions": predictions,
                "technical_analysis": {
                    "trend": round(float(trend), 2),
                    "volatility": round(float(volatility), 2),
                    "rsi": round(float(rsi), 2),
                    "momentum": round(float(momentum), 2),
                },
                "recommendation": recommendation,
                "model_version": self.model_version,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ [ML] Prediction error for {stock_symbol}: {e}")
            return self._create_error_response()

    def _calculate_volatility(self, prices: np.ndarray) -> float:
        """Calculate historical volatility as percentage."""
        if len(prices) < 2:
            return 1.0
        returns = np.diff(prices) / prices[:-1]
        volatility = float(np.std(returns) * 100)
        return min(volatility, 100.0)  # Cap at 100%

    def _calculate_trend(self, prices: np.ndarray) -> float:
        """Calculate price trend using linear regression."""
        if len(prices) < 2:
            return 0.0
        x = np.arange(len(prices))
        coefficients = np.polyfit(x, prices, 1)  # Linear fit
        trend = (coefficients[0] / prices[-1]) * 100  # As percentage
        return float(np.clip(trend, -50, 50))  # Cap between -50% and +50%

    def _calculate_rsi(self, prices: np.ndarray, period: int = 7) -> float:
        """
        Calculate Relative Strength Index (RSI) - measures momentum/overbought-oversold.
        RSI range: 0-100, with 70+ = overbought, 30- = oversold, 50 = neutral
        Using period=7 instead of 14 for better responsiveness on smaller datasets.
        """
        if len(prices) < period:
            # Adaptive: use available data if less than period
            if len(prices) < 2:
                return 50.0  # Need at least 2 points for RSI
            period = len(prices) - 1  # Use all available deltas

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:]) if len(gains) >= period else np.mean(gains)
        avg_loss = np.mean(losses[-period:]) if len(losses) >= period else np.mean(losses)

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(np.clip(rsi, 0, 100))

    def _calculate_momentum(self, prices: np.ndarray, period: int = 5) -> float:
        """Calculate price momentum (rate of change over last N periods)."""
        if len(prices) < period:
            # For short data, use 1-period momentum to measure recent change
            if len(prices) < 2:
                return 0.0
            momentum = ((prices[-1] - prices[-2]) / prices[-2]) * 100
            return float(np.clip(momentum, -100, 100))
        
        # Calculate momentum as percentage change over period
        momentum = ((prices[-1] - prices[-period]) / prices[-period]) * 100
        
        # Also factor in recent acceleration (how fast it's changing now)
        if len(prices) >= 3:
            recent_change = ((prices[-1] - prices[-2]) / prices[-2]) * 100
            # Weight: 70% overall trend, 30% recent acceleration
            momentum = (momentum * 0.7) + (recent_change * 0.3)
        
        return float(np.clip(momentum, -100, 100))

    def _generate_recommendation(
        self, price_change: float, rsi: float, momentum: float, confidence: float
    ) -> str:
        """Generate buy/sell/hold recommendation based on technical indicators."""
        # Scoring system: accumulate buy/sell signals
        buy_score = 0.0
        sell_score = 0.0
        
        # RSI analysis (0-100 scale) - more lenient
        if rsi > 70:
            sell_score += 3  # Overbought
        elif rsi > 55:
            sell_score += 1.5  # Leaning overbought
        elif rsi < 30:
            buy_score += 3  # Oversold
        elif rsi < 45:
            buy_score += 1.5  # Leaning oversold
        
        # Momentum analysis (percentage change) - lower thresholds
        if momentum > 1.5:
            buy_score += 2  # Positive momentum
        elif momentum > 0.2:
            buy_score += 1  # Slight positive
        elif momentum < -1.5:
            sell_score += 2  # Negative momentum
        elif momentum < -0.2:
            sell_score += 1  # Slight negative
        
        # Price trend analysis (percentage change)
        if price_change > 0.5:
            buy_score += 1
        elif price_change < -0.5:
            sell_score += 1
        
        # Confidence factor (boost moderate signals)
        if confidence > 0.75:
            # Strong signals - tiebreaker favor confidence
            if buy_score == sell_score:
                buy_score += 0.5
        
        # Decision logic - more balanced
        diff = buy_score - sell_score
        if diff > 1.2:
            return "BUY"
        elif diff < -1.2:
            return "SELL"
        else:
            return "HOLD"

    def _create_error_response(self) -> Dict:
        """Create standardized error response."""
        return {
            "status": "error",
            "message": "Failed to generate predictions",
            "predictions": [],
            "model_version": self.model_version,
            "generated_at": datetime.utcnow().isoformat(),
        }


# Global instance
ml_engine = MLPredictionEngine()
