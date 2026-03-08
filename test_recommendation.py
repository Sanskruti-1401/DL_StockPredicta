#!/usr/bin/env python3
"""
Test the recommendation system directly from the backend.
Run with: python test_recommendation.py (from StockPredictor root)
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Point to backend directory
backend_dir = Path(__file__).parent / 'backend'
env_path = backend_dir / '.env'

# Load env and set correct database path
if env_path.exists():
    load_dotenv(env_path)

# Override DATABASE_URL to use backend's database file (where backend actually stores data)
os.environ['DATABASE_URL'] = f'sqlite:///{backend_dir / "test.db"}'

# NOW add backend to path and import
sys.path.insert(0, str(backend_dir))

from app.db.base import get_db, engine, Base
from app.db.models import Stock, PriceHistory
from app.services.ml_prediction import ml_engine
from datetime import datetime, timedelta
import numpy as np

def test_recommendations():
    """Test recommendation generation for all stocks."""
    
    print("=" * 70)
    print("STOCK PREDICTOR - BACKEND RECOMMENDATION TEST")
    print("=" * 70)
    print()
    
    # Initialize database
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    
    try:
        # Get all stocks
        stocks = db.query(Stock).all()
        
        if not stocks:
            print("ERROR: No stocks found in database!")
            print("Run seed script first: python -c 'from app.db.base import seed_stocks; seed_stocks()'")
            return
        
        print(f"Found {len(stocks)} stocks. Testing recommendations...\n")
        
        for stock in stocks:
            print(f"{stock.symbol} ({stock.name})")
            print("-" * 70)
            
            # Get last 30 days of price data
            cutoff = datetime.utcnow() - timedelta(days=30)
            prices_db = db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock.id,
                PriceHistory.date >= cutoff
            ).order_by(PriceHistory.date.asc()).all()
            
            if not prices_db:
                print("  ERROR: No price data for this stock!\n")
                continue
            
            # Extract data
            historical_prices = np.array([float(p.close_price) for p in prices_db])
            historical_dates = [p.date for p in prices_db]
            
            print(f"  Data Points: {len(historical_prices)} records")
            print(f"  Date Range: {historical_dates[0].date()} to {historical_dates[-1].date()}")
            print(f"  Price Range: ${historical_prices.min():.2f} - ${historical_prices.max():.2f}")
            
            # Generate prediction
            try:
                prediction = ml_engine.predict_price(
                    historical_prices=historical_prices.tolist(),
                    historical_dates=historical_dates,
                    stock_symbol=stock.symbol,
                    prediction_hours=24
                )
                
                if prediction['status'] == 'success':
                    print()
                    print(f"  Current Price: ${prediction['current_price']:.2f}")
                    print()
                    
                    # Technical Analysis
                    tech = prediction['technical_analysis']
                    print("  TECHNICAL ANALYSIS:")
                    print(f"    - Trend:      {tech['trend']:+.2f}%")
                    print(f"    - Volatility: {tech['volatility']:.2f}%")
                    print(f"    - RSI:        {tech['rsi']:.1f}")
                    print(f"    - Momentum:   {tech['momentum']:+.2f}%")
                    print()
                    
                    # Recommendation
                    rec = prediction['recommendation']
                    rec_emoji = '👍' if rec == 'BUY' else '👎' if rec == 'SELL' else '➡️'
                    print(f"  RECOMMENDATION: {rec_emoji} {rec}")
                    
                    # Show reasoning
                    rsi = tech['rsi']
                    momentum = tech['momentum']
                    trend = tech['trend']
                    
                    print()
                    print("  REASONING:")
                    if rsi > 70:
                        print(f"    • RSI {rsi:.1f} > 70 = OVERBOUGHT → SELL signal")
                    elif rsi < 30:
                        print(f"    • RSI {rsi:.1f} < 30 = OVERSOLD → BUY signal")
                    else:
                        print(f"    • RSI {rsi:.1f} in neutral zone (30-70)")
                    
                    if trend > 2 and momentum > 5:
                        print(f"    • Strong uptrend: Trend={trend:+.2f}%, Momentum={momentum:+.2f}% → BUY")
                    elif trend < -2 and momentum < -5:
                        print(f"    • Strong downtrend: Trend={trend:+.2f}%, Momentum={momentum:+.2f}% → SELL")
                    else:
                        print(f"    • Mixed signals: Trend={trend:+.2f}%, Momentum={momentum:+.2f}% → HOLD")
                    
                    # Predictions
                    print()
                    print(f"  FORECAST ({len(prediction['predictions'])} hours ahead):")
                    first_pred = prediction['predictions'][0]
                    last_pred = prediction['predictions'][-1]
                    print(f"    First: ${first_pred['price']:.2f} (confidence {first_pred['confidence']:.0%})")
                    print(f"    Last:  ${last_pred['price']:.2f} (confidence {last_pred['confidence']:.0%})")
                else:
                    print(f"  ERROR: {prediction.get('message', 'Unknown error')}\n")
                    
            except Exception as e:
                print(f"  EXCEPTION: {e}\n")
            
            print()
        
        print("=" * 70)
        print("Test completed!")
        print("=" * 70)
        
    finally:
        db.close()

if __name__ == "__main__":
    test_recommendations()
