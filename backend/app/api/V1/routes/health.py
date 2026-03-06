"""
Health check routes.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ....db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Stock Predictor API",
        "version": "1.0.0",
    }


@router.get("/health/db")
async def health_db(db: Session = Depends(get_db)):
    """Check database connectivity."""
    try:
        # Simple query to check DB connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
