"""
Risk assessment and management service.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import numpy as np
from sqlalchemy.orm import Session

from ..db.models import Stock, RiskMetric, PriceHistory
from ..api.V1.schemas.risk import RiskMetricSchema

logger = logging.getLogger(__name__)


class RiskService:
    """Service for risk assessment and portfolio risk management."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_volatility(self, stock_id: int, period_days: int = 30) -> Optional[float]:
        """
        Calculate stock volatility (standard deviation of returns).
        
        Args:
            stock_id: Stock ID
            period_days: Period for calculation
            
        Returns:
            Volatility value
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            price_data = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.date >= cutoff_date
            ).order_by(PriceHistory.date.asc()).all()
            
            if len(price_data) < 2:
                return None
            
            prices = [p.close_price for p in price_data]
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
            
            return float(volatility)
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return None

    def calculate_max_drawdown(self, stock_id: int, period_days: int = 365) -> Optional[float]:
        """
        Calculate maximum drawdown over a period.
        
        Args:
            stock_id: Stock ID
            period_days: Period for calculation
            
        Returns:
            Max drawdown value
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            price_data = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.date >= cutoff_date
            ).order_by(PriceHistory.date.asc()).all()
            
            if len(price_data) < 2:
                return None
            
            prices = np.array([p.close_price for p in price_data])
            cumulative_max = np.maximum.accumulate(prices)
            drawdown = (prices - cumulative_max) / cumulative_max
            max_drawdown = np.min(drawdown)
            
            return float(abs(max_drawdown))
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return None

    def calculate_sharpe_ratio(self, stock_id: int, risk_free_rate: float = 0.02, period_days: int = 365) -> Optional[float]:
        """
        Calculate Sharpe ratio.
        
        Args:
            stock_id: Stock ID
            risk_free_rate: Annual risk-free rate
            period_days: Period for calculation
            
        Returns:
            Sharpe ratio value
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            price_data = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.date >= cutoff_date
            ).order_by(PriceHistory.date.asc()).all()
            
            if len(price_data) < 2:
                return None
            
            prices = np.array([p.close_price for p in price_data])
            returns = np.diff(prices) / prices[:-1]
            
            annual_return = np.mean(returns) * 252
            annual_volatility = np.std(returns) * np.sqrt(252)
            
            if annual_volatility == 0:
                return None
            
            sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
            return float(sharpe_ratio)
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return None

    def calculate_value_at_risk(self, stock_id: int, confidence: float = 0.95, period_days: int = 30) -> Optional[float]:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            stock_id: Stock ID
            confidence: Confidence level (0-1)
            period_days: Period for calculation
            
        Returns:
            VaR value
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            price_data = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.date >= cutoff_date
            ).order_by(PriceHistory.date.asc()).all()
            
            if len(price_data) < 2:
                return None
            
            prices = np.array([p.close_price for p in price_data])
            returns = np.diff(prices) / prices[:-1]
            
            var = np.quantile(returns, 1 - confidence)
            return float(abs(var))
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return None

    def assess_risk_level(self, volatility: Optional[float], beta: Optional[float], sharpe_ratio: Optional[float]) -> str:
        """
        Assess overall risk level based on metrics.
        
        Args:
            volatility: Stock volatility
            beta: Beta coefficient
            sharpe_ratio: Sharpe ratio
            
        Returns:
            Risk level: LOW, MEDIUM, HIGH, VERY_HIGH
        """
        try:
            risk_score = 0.0
            
            # Volatility contribution (30%)
            if volatility:
                if volatility < 0.2:
                    risk_score += 0.0
                elif volatility < 0.4:
                    risk_score += 0.3
                elif volatility < 0.6:
                    risk_score += 0.6
                else:
                    risk_score += 0.9
            
            # Beta contribution (30%)
            if beta:
                if beta < 0.8:
                    risk_score += 0.0
                elif beta < 1.2:
                    risk_score += 0.3
                elif beta < 1.5:
                    risk_score += 0.6
                else:
                    risk_score += 0.9
            
            # Sharpe ratio contribution (40%)
            if sharpe_ratio:
                if sharpe_ratio > 1.0:
                    risk_score += 0.0
                elif sharpe_ratio > 0.5:
                    risk_score += 0.4
                elif sharpe_ratio > 0.0:
                    risk_score += 0.8
                else:
                    risk_score += 1.2
            
            # Normalize score
            risk_score = min(risk_score / 3, 1.0)
            
            if risk_score < 0.25:
                return "LOW"
            elif risk_score < 0.5:
                return "MEDIUM"
            elif risk_score < 0.75:
                return "HIGH"
            else:
                return "VERY_HIGH"
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return "MEDIUM"

    def calculate_return(self, stock_id: int, days: int) -> Optional[float]:
        """
        Calculate return over specified period.
        
        Args:
            stock_id: Stock ID
            days: Number of days
            
        Returns:
            Return percentage
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            current_price = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id
            ).order_by(PriceHistory.date.desc()).first()
            
            past_price = self.db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock_id,
                PriceHistory.date <= cutoff_date
            ).order_by(PriceHistory.date.desc()).first()
            
            if current_price and past_price:
                return_pct = ((current_price.close_price - past_price.close_price) / past_price.close_price) * 100
                return float(return_pct)
            
            return None
        except Exception as e:
            logger.error(f"Error calculating return: {e}")
            return None

    def create_risk_metric(self, stock_id: int, stock: Stock) -> RiskMetric:
        """Create and store risk metrics for a stock."""
        try:
            volatility = self.calculate_volatility(stock_id)
            max_drawdown = self.calculate_max_drawdown(stock_id)
            sharpe_ratio = self.calculate_sharpe_ratio(stock_id)
            var = self.calculate_value_at_risk(stock_id)
            
            risk_level = self.assess_risk_level(volatility, stock.beta, sharpe_ratio)
            
            # Calculate risk score
            risk_scores = []
            if volatility:
                risk_scores.append(min(volatility * 50, 100))
            if max_drawdown:
                risk_scores.append(min(max_drawdown * 100, 100))
            
            risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 50.0
            
            metric = RiskMetric(
                stock_id=stock_id,
                date=datetime.utcnow(),
                volatility=volatility or 0.0,
                beta=stock.beta,
                value_at_risk=var,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                return_1_month=self.calculate_return(stock_id, 30),
                return_3_month=self.calculate_return(stock_id, 90),
                return_6_month=self.calculate_return(stock_id, 180),
                return_1_year=self.calculate_return(stock_id, 365),
                risk_level=risk_level,
                risk_score=risk_score,
            )
            
            self.db.add(metric)
            self.db.commit()
            self.db.refresh(metric)
            logger.info(f"Risk metrics created for stock {stock_id}")
            return metric
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating risk metric: {e}")
            raise

    def get_latest_risk_metric(self, stock_id: int) -> Optional[RiskMetric]:
        """Get the latest risk metric for a stock."""
        return self.db.query(RiskMetric).filter(
            RiskMetric.stock_id == stock_id
        ).order_by(RiskMetric.date.desc()).first()

    def get_risk_alerts(self, stock_id: int) -> List[str]:
        """Generate risk alerts for a stock."""
        alerts = []
        try:
            risk_metric = self.get_latest_risk_metric(stock_id)
            
            if not risk_metric:
                return alerts
            
            # High volatility alert
            if risk_metric.volatility and risk_metric.volatility > 0.5:
                alerts.append(f"High volatility detected: {risk_metric.volatility:.2%}")
            
            # Large drawdown alert
            if risk_metric.max_drawdown and risk_metric.max_drawdown > 0.3:
                alerts.append(f"Large drawdown: {risk_metric.max_drawdown:.2%}")
            
            # Poor Sharpe ratio alert
            if risk_metric.sharpe_ratio and risk_metric.sharpe_ratio < 0.5:
                alerts.append("Poor risk-adjusted returns (Sharpe ratio < 0.5)")
            
            # Recent negative returns alert
            if risk_metric.return_1_month and risk_metric.return_1_month < -10:
                alerts.append(f"Significant negative return this month: {risk_metric.return_1_month:.2f}%")
        
        except Exception as e:
            logger.error(f"Error generating risk alerts: {e}")
        
        return alerts

    def calculate_portfolio_risk(self, stock_ids: List[int], weights: Optional[List[float]] = None) -> Dict:
        """
        Calculate portfolio-level risk metrics.
        
        Args:
            stock_ids: List of stock IDs
            weights: Portfolio weights (default equal-weighted)
            
        Returns:
            Portfolio risk metrics
        """
        try:
            if not stock_ids:
                return {}
            
            if weights is None:
                weights = [1.0 / len(stock_ids)] * len(stock_ids)
            
            volatilities = []
            betas = []
            
            for stock_id in stock_ids:
                stock = self.db.query(Stock).filter(Stock.id == stock_id).first()
                if stock:
                    vol = self.calculate_volatility(stock_id)
                    if vol:
                        volatilities.append(vol)
                    if stock.beta:
                        betas.append(stock.beta)
            
            portfolio_volatility = np.average(volatilities, weights=weights[:len(volatilities)]) if volatilities else 0.0
            portfolio_beta = np.average(betas, weights=weights[:len(betas)]) if betas else 1.0
            
            return {
                "portfolio_volatility": float(portfolio_volatility),
                "portfolio_beta": float(portfolio_beta),
                "num_stocks": len(stock_ids),
            }
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}")
            return {}
