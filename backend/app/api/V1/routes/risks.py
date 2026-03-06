"""
Risk assessment and dashboard routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ....db.base import get_db
from ....db.models import Stock, RiskMetric, User
from ....services.risk import RiskService
from ..schemas.risk import (
    RiskMetricSchema, RiskDashboardSchema, RiskAnalysisSchema,
    PortfolioRiskSchema, StressTestSchema
)
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/risks", tags=["Risk Management"])


@router.get("/stocks/{stock_id}")
async def get_stock_risk(
    stock_id: int,
    db: Session = Depends(get_db),
    risk_service: RiskService = Depends(lambda db=Depends(get_db): RiskService(db))
):
    """Get risk metrics for a stock."""
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        metric = risk_service.get_latest_risk_metric(stock_id)
        
        if not metric:
            raise HTTPException(status_code=404, detail="No risk metrics available")
        
        return {
            "id": metric.id,
            "stock_id": metric.stock_id,
            "date": metric.date,
            "volatility": metric.volatility,
            "beta": metric.beta,
            "value_at_risk": metric.value_at_risk,
            "max_drawdown": metric.max_drawdown,
            "sharpe_ratio": metric.sharpe_ratio,
            "sortino_ratio": metric.sortino_ratio,
            "return_1_month": metric.return_1_month,
            "return_3_month": metric.return_3_month,
            "return_6_month": metric.return_6_month,
            "return_1_year": metric.return_1_year,
            "risk_level": metric.risk_level,
            "risk_score": metric.risk_score,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock risk: {e}")
        raise HTTPException(status_code=500, detail="Error getting stock risk")


@router.get("/stocks/{stock_id}/dashboard")
async def get_risk_dashboard(
    stock_id: int,
    db: Session = Depends(get_db),
    risk_service: RiskService = Depends(lambda db=Depends(get_db): RiskService(db))
):
    """Get risk dashboard for a stock."""
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        metric = risk_service.get_latest_risk_metric(stock_id)
        
        if not metric:
            raise HTTPException(status_code=404, detail="No risk data available")
        
        alerts = risk_service.get_risk_alerts(stock_id)
        
        return {
            "stock_symbol": stock.symbol,
            "current_price": 0.0,  # Would fetch current price
            "risk_level": metric.risk_level,
            "risk_score": metric.risk_score,
            "key_metrics": {
                "volatility": metric.volatility,
                "beta": metric.beta,
                "value_at_risk": metric.value_at_risk,
                "max_drawdown": metric.max_drawdown,
                "sharpe_ratio": metric.sharpe_ratio,
            },
            "alerts": alerts,
            "recommendations": generate_risk_recommendations(metric),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error getting risk dashboard")


@router.post("/stocks/{stock_id}/calculate")
async def calculate_risk_metrics(
    stock_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    risk_service: RiskService = Depends(lambda db=Depends(get_db): RiskService(db))
):
    """Calculate risk metrics for a stock."""
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        # Calculate and store metrics
        metric = risk_service.create_risk_metric(stock_id, stock)
        
        return {
            "message": "Risk metrics calculated successfully",
            "stock_symbol": stock.symbol,
            "risk_score": metric.risk_score,
            "risk_level": metric.risk_level,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Error calculating risk metrics")


@router.get("/stocks/{stock_id}/history")
async def get_risk_history(
    stock_id: int,
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get historical risk metrics for a stock."""
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        metrics = db.query(RiskMetric).filter(
            RiskMetric.stock_id == stock_id,
            RiskMetric.date >= cutoff_date
        ).order_by(RiskMetric.date.desc()).all()
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No historical risk data available")
        
        # Calculate trend
        latest_score = metrics[0].risk_score if metrics else 0
        earliest_score = metrics[-1].risk_score if len(metrics) > 1 else latest_score
        
        trend = "INCREASING" if latest_score > earliest_score else "DECREASING" if latest_score < earliest_score else "STABLE"
        
        return {
            "stock_symbol": stock.symbol,
            "period_days": days,
            "risk_metrics_history": [
                {
                    "date": m.date,
                    "volatility": m.volatility,
                    "beta": m.beta,
                    "risk_score": m.risk_score,
                    "risk_level": m.risk_level,
                }
                for m in metrics
            ],
            "risk_trend": trend,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk history: {e}")
        raise HTTPException(status_code=500, detail="Error getting risk history")


@router.get("/stocks/{stock_id}/stress-test")
async def get_stress_test(
    stock_id: int,
    db: Session = Depends(get_db),
    risk_service: RiskService = Depends(lambda db=Depends(get_db): RiskService(db))
):
    """Get stress test scenarios for a stock."""
    try:
        # Verify stock exists
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        metric = risk_service.get_latest_risk_metric(stock_id)
        
        if not metric:
            raise HTTPException(status_code=404, detail="No data available for stress test")
        
        # Get current price
        from ...db.models import PriceHistory
        latest_price = db.query(PriceHistory).filter(
            PriceHistory.stock_id == stock_id
        ).order_by(PriceHistory.date.desc()).first()
        
        current_price = latest_price.close_price if latest_price else 0.0
        
        return {
            "stock_symbol": stock.symbol,
            "base_scenario": {
                "price": current_price,
                "return": 0.0,
                "description": "Current market conditions"
            },
            "bull_case": {
                "price": current_price * 1.20,
                "return": 20.0,
                "description": "+20% market movement"
            },
            "bear_case": {
                "price": current_price * 0.80,
                "return": -20.0,
                "description": "-20% market movement"
            },
            "extreme_case": {
                "price": current_price * 0.60,
                "return": -40.0,
                "description": "-40% market crash"
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stress test: {e}")
        raise HTTPException(status_code=500, detail="Error getting stress test")


@router.get("/ranking")
async def get_risk_ranking(
    limit: int = Query(20, ge=1, le=100),
    sector: str | None = None,
    db: Session = Depends(get_db)
):
    """Get stocks ranked by risk level."""
    try:
        query = db.query(Stock, RiskMetric).join(
            RiskMetric, Stock.id == RiskMetric.stock_id
        ).order_by(RiskMetric.risk_score.desc()).limit(limit)
        
        if sector:
            query = query.filter(Stock.sector == sector)
        
        results = query.all()
        
        return [
            {
                "stock_id": stock.id,
                "symbol": stock.symbol,
                "name": stock.name,
                "sector": stock.sector,
                "risk_level": metric.risk_level,
                "risk_score": metric.risk_score,
                "volatility": metric.volatility,
                "beta": metric.beta,
            }
            for stock, metric in results
        ]
    except Exception as e:
        logger.error(f"Error getting risk ranking: {e}")
        raise HTTPException(status_code=500, detail="Error getting risk ranking")


def generate_risk_recommendations(metric: RiskMetric) -> list[str]:
    """Generate risk mitigation recommendations."""
    recommendations = []
    
    if metric.risk_score > 75:
        recommendations.append("High risk - Consider diversifying or reducing position size")
    elif metric.risk_score > 50:
        recommendations.append("Moderate risk - Monitor closely for any changes")
    
    if metric.volatility and metric.volatility > 0.5:
        recommendations.append("High volatility - Use stop-loss orders")
    
    if metric.max_drawdown and metric.max_drawdown > 0.3:
        recommendations.append("Large drawdowns - Consider setting profit targets")
    
    if metric.sharpe_ratio and metric.sharpe_ratio < 0.5:
        recommendations.append("Poor risk-adjusted returns - Review investment thesis")
    
    if not recommendations:
        recommendations.append("Risk metrics are stable - Continue monitoring")
    
    return recommendations
