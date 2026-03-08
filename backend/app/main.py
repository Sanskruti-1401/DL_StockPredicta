"""
FastAPI application factory and startup/shutdown handlers.
"""
from contextlib import asynccontextmanager
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .core.config import settings
from .core.logging import setup_logging
from .db.base import init_db, get_db
from .db.models import Stock
from .api.V1.routes import auth, health, stocks, news, risks, refresh, seed, predictions, sentiment, websocket
from .workers.background_tasks import update_stock_price_data, update_sentiment_data, prefetch_predictions

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting up Stock Predictor API...")
    await init_db()
    logger.info("Database initialized")
    
    # Start background tasks (suppress their startup logging)
    logger.info("Starting background tasks...")
    price_update_task = asyncio.create_task(update_stock_price_data())
    sentiment_update_task = asyncio.create_task(update_sentiment_data())
    prediction_prefetch_task = asyncio.create_task(prefetch_predictions())
    logger.info("Background tasks started")
    
    # Auto-seed stocks if database is empty
    try:
        db = next(get_db())
        stock_count = db.query(Stock).count()
        if stock_count == 0:
            logger.info("No stocks found in database, auto-seeding...")
            
            # Seed the 10 stocks
            from .api.V1.routes.seed import SEED_STOCKS, generate_price_history
            from .db.models import PriceHistory
            
            created = 0
            for stock_data in SEED_STOCKS:
                try:
                    stock = Stock(**stock_data)
                    db.add(stock)
                    db.commit()
                    db.refresh(stock)  # Get the stock ID
                    
                    # Also seed price history for this stock
                    price_history = generate_price_history(stock.id, stock.symbol, days=90)
                    for price_record in price_history:
                        db.add(price_record)
                    db.commit()
                    
                    created += 1
                    logger.info(f"Seeded stock: {stock_data['symbol']}")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Failed to seed {stock_data['symbol']}: {e}")
            
            logger.info(f"Auto-seeding completed: {created} stocks with price history created")
        else:
            logger.info(f"Found {stock_count} stocks in database")
    except Exception as e:
        logger.warning(f"Auto-seed check failed (may be first startup): {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down background tasks...")
    price_update_task.cancel()
    sentiment_update_task.cancel()
    prediction_prefetch_task.cancel()
    logger.info("Stock Predictor API shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Stock Predictor API",
        description="Full-stack stock prediction and analysis platform",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
    app.include_router(stocks.router, prefix="/api/v1", tags=["Stocks"])
    app.include_router(news.router, prefix="/api/v1", tags=["News"])
    app.include_router(risks.router, prefix="/api/v1", tags=["Risks"])
    app.include_router(refresh.router, prefix="/api/v1", tags=["Data Refresh"])
    app.include_router(seed.router, prefix="/api/v1", tags=["Seeding"])
    app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
    app.include_router(sentiment.router, prefix="/api/v1", tags=["Sentiment"])
    app.include_router(websocket.router, tags=["WebSocket"])

    logger.info("FastAPI application created successfully")
    return app


app = create_app()
