"""
Technical indicators calculation and analysis service.
"""
import logging
from datetime import datetime
from typing import Optional, List
import numpy as np
from sqlalchemy.orm import Session

from ..db.models import Stock, TechnicalIndicator, PriceHistory

logger = logging.getLogger(__name__)


class IndicatorsService:
    """Service for calculating technical indicators."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: List of prices
            period: Period for SMA
            
        Returns:
            SMA value
        """
        if len(prices) < period:
            return None
        return np.mean(prices[-period:])

    def calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: List of prices
            period: Period for EMA
            
        Returns:
            EMA value
        """
        if len(prices) < period:
            return None
        
        sma = np.mean(prices[:period])
        multiplier = 2 / (period + 1)
        ema = sma
        
        for price in prices[period:]:
            ema = price * multiplier + ema * (1 - multiplier)
        
        return ema

    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index.
        
        Args:
            prices: List of prices
            period: Period for RSI
            
        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0).mean()
        losses = -np.where(deltas < 0, deltas, 0).mean()
        
        if losses == 0:
            return 100.0 if gains > 0 else 0.0
        
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)

    def calculate_macd(self, prices: List[float]) -> tuple[Optional[float], Optional[float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: List of prices
            
        Returns:
            Tuple of (MACD, Signal line)
        """
        if len(prices) < 26:
            return None, None
        
        ema12 = self.calculate_ema(prices, 12)
        ema26 = self.calculate_ema(prices, 26)
        
        if ema12 is None or ema26 is None:
            return None, None
        
        macd = ema12 - ema26
        
        # Signal line is 9-period EMA of MACD
        signal = self.calculate_ema([macd], 9) if len(prices) >= 35 else None
        
        return float(macd), signal

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> dict:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: List of prices
            period: Period for BB
            std_dev: Standard deviation multiplier
            
        Returns:
            Dictionary with upper, middle, lower bands
        """
        if len(prices) < period:
            return {}
        
        middle = self.calculate_sma(prices, period)
        if middle is None:
            return {}
        
        std = np.std(prices[-period:])
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            "upper": float(upper),
            "middle": float(middle),
            "lower": float(lower),
        }

    def calculate_atr(self, high_prices: List[float], low_prices: List[float], close_prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate Average True Range.
        
        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of close prices
            period: Period for ATR
            
        Returns:
            ATR value
        """
        if len(high_prices) < period:
            return None
        
        tr_values = []
        for i in range(len(high_prices)):
            high_low = high_prices[i] - low_prices[i]
            high_close = abs(high_prices[i] - close_prices[i-1]) if i > 0 else high_low
            low_close = abs(low_prices[i] - close_prices[i-1]) if i > 0 else high_low
            
            tr = max(high_low, high_close, low_close)
            tr_values.append(tr)
        
        atr = np.mean(tr_values[-period:])
        return float(atr)

    def calculate_obv(self, prices: List[float], volumes: List[float]) -> Optional[float]:
        """
        Calculate On-Balance Volume.
        
        Args:
            prices: List of close prices
            volumes: List of volumes
            
        Returns:
            OBV value
        """
        if len(prices) != len(volumes) or len(prices) < 2:
            return None
        
        obv = volumes[0]
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                obv += volumes[i]
            elif prices[i] < prices[i-1]:
                obv -= volumes[i]
        
        return float(obv)

    def calculate_all_indicators(self, stock_id: int) -> Optional[TechnicalIndicator]:
        """
        Calculate all technical indicators for a stock.
        
        Args:
            stock_id: Stock ID
            
        Returns:
            TechnicalIndicator record
        """
        try:
            # Get last 100 days of price data
            price_data = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id
            ).order_by(PriceHistory.date.asc()).limit(100).all()
            
            if len(price_data) < 2:
                return None
            
            closes = [p.close_price for p in price_data]
            highs = [p.high_price for p in price_data]
            lows = [p.low_price for p in price_data]
            volumes = [p.volume for p in price_data if p.volume]
            
            # Calculate indicators
            sma_20 = self.calculate_sma(closes, 20)
            sma_50 = self.calculate_sma(closes, 50)
            sma_200 = self.calculate_sma(closes, 200)
            ema_12 = self.calculate_ema(closes, 12)
            ema_26 = self.calculate_ema(closes, 26)
            rsi = self.calculate_rsi(closes)
            macd, macd_signal = self.calculate_macd(closes)
            bb = self.calculate_bollinger_bands(closes)
            atr = self.calculate_atr(highs, lows, closes)
            obv = self.calculate_obv(closes, volumes) if volumes else None
            
            # Volatility
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            
            # Create indicator record
            indicator = TechnicalIndicator(
                stock_id=stock_id,
                date=datetime.utcnow(),
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                sma_20=sma_20,
                sma_50=sma_50,
                sma_200=sma_200,
                ema_12=ema_12,
                ema_26=ema_26,
                bb_upper=bb.get("upper"),
                bb_middle=bb.get("middle"),
                bb_lower=bb.get("lower"),
                atr=atr,
                obv=obv,
                volatility=volatility,
                ad_line=None,  # Could calculate Acc/Dist
            )
            
            self.db.add(indicator)
            self.db.commit()
            self.db.refresh(indicator)
            logger.info(f"Calculated indicators for stock {stock_id}")
            return indicator
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error calculating indicators: {e}")
            return None

    def get_latest_indicators(self, stock_id: int) -> Optional[TechnicalIndicator]:
        """Get the latest technical indicators for a stock."""
        return self.db.query(TechnicalIndicator).filter(
            TechnicalIndicator.stock_id == stock_id
        ).order_by(TechnicalIndicator.date.desc()).first()

    def get_signal_strength(self, stock_id: int) -> dict:
        """
        Get overall signal strength based on multiple indicators.
        
        Args:
            stock_id: Stock ID
            
        Returns:
            Signal analysis dictionary
        """
        try:
            indicators = self.get_latest_indicators(stock_id)
            if not indicators:
                return {}
            
            signals = {
                "bullish": 0,
                "bearish": 0,
                "neutral": 0,
            }
            
            # RSI signal
            if indicators.rsi:
                if indicators.rsi < 30:
                    signals["bullish"] += 1
                elif indicators.rsi > 70:
                    signals["bearish"] += 1
                else:
                    signals["neutral"] += 1
            
            # MACD signal
            if indicators.macd and indicators.macd_signal:
                if indicators.macd > indicators.macd_signal:
                    signals["bullish"] += 1
                else:
                    signals["bearish"] += 1
            
            # Moving average signal
            if indicators.sma_50 and indicators.sma_200:
                if indicators.sma_50 > indicators.sma_200:
                    signals["bullish"] += 1
                else:
                    signals["bearish"] += 1
            
            # Bollinger Bands signal
            if indicators.bb_upper and indicators.bb_middle and indicators.bb_lower:
                latest_price = self.db.query(PriceHistory).filter(
                    PriceHistory.stock_id == stock_id
                ).order_by(PriceHistory.date.desc()).first()
                
                if latest_price:
                    if latest_price.close_price < indicators.bb_lower:
                        signals["bullish"] += 1
                    elif latest_price.close_price > indicators.bb_upper:
                        signals["bearish"] += 1
                    else:
                        signals["neutral"] += 1
            
            # Determine overall signal
            total_signals = sum(signals.values())
            if total_signals == 0:
                overall_signal = "NEUTRAL"
            elif signals["bullish"] > signals["bearish"]:
                overall_signal = "BULLISH"
            elif signals["bearish"] > signals["bullish"]:
                overall_signal = "BEARISH"
            else:
                overall_signal = "NEUTRAL"
            
            signals["overall"] = overall_signal
            signals["strength"] = (max(signals["bullish"], signals["bearish"]) / total_signals * 100) if total_signals > 0 else 0
            
            return signals
        except Exception as e:
            logger.error(f"Error getting signal strength: {e}")
            return {}

    def batch_calculate_indicators(self, stock_ids: List[int]) -> dict:
        """
        Calculate indicators for multiple stocks.
        
        Args:
            stock_ids: List of stock IDs
            
        Returns:
            Calculation statistics
        """
        stats = {
            "total": len(stock_ids),
            "calculated": 0,
            "failed": 0,
        }
        
        try:
            for stock_id in stock_ids:
                try:
                    result = self.calculate_all_indicators(stock_id)
                    if result:
                        stats["calculated"] += 1
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Error calculating indicators for stock {stock_id}: {e}")
            
            return stats
        except Exception as e:
            logger.error(f"Error in batch_calculate_indicators: {e}")
            return stats
