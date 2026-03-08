#!/usr/bin/env python3
"""
Comprehensive fix script for Stock Predictor.
Checks backend, database, and APIs.
Run with: python fix_and_test.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Force SQLite database path
os.environ['DATABASE_URL'] = f'sqlite:///{backend_path / "test.db"}'

from app.db.base import engine, SessionLocal, init_db
from app.db.models import Base, Stock, PriceHistory
from app.services.ml_prediction import ml_engine
from app.services.sentiment import sentiment_analyzer
from datetime import datetime, timedelta
import numpy as np

def check_database():
    """Check if database has stocks and price data."""
    print("\n" + "="*70)
    print("CHECKING DATABASE")
    print("="*70)
    
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        
        # Check stocks
        stocks = db.query(Stock).all()
        print(f"✅ Database connected")
        print(f"📊 Found {len(stocks)} stocks")
        
        if len(stocks) == 0:
            print("❌ No stocks in database - need to seed")
            db.close()
            return False
        
        # Check price data for each stock
        for stock in stocks[:3]:  # Check first 3
            prices = db.query(PriceHistory).filter(
                PriceHistory.stock_id == stock.id
            ).count()
            print(f"  - {stock.symbol}: {prices} price records")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def seed_database():
    """Seed database with initial data."""
    print("\n" + "="*70)
    print("SEEDING DATABASE")
    print("="*70)
    
    try:
        from app.api.V1.routes.seed import SEED_STOCKS, generate_price_history
        
        db = SessionLocal()
        
        # Clear existing data
        db.query(PriceHistory).delete()
        db.query(Stock).delete()
        db.commit()
        print("✅ Cleared existing data")
        
        # Seed stocks
        created = 0
        for stock_data in SEED_STOCKS:
            try:
                stock = Stock(**stock_data)
                db.add(stock)
                db.commit()
                db.refresh(stock)
                
                # Seed price history - 90 days for better technical analysis
                price_history = generate_price_history(stock.id, stock.symbol, days=90)
                for price_record in price_history:
                    db.add(price_record)
                db.commit()
                
                created += 1
                print(f"✅ Seeded {stock_data['symbol']} with 90 days of data")
            except Exception as e:
                db.rollback()
                print(f"❌ Failed to seed {stock_data['symbol']}: {e}")
        
        print(f"\n✅ Seeding complete: {created} stocks created")
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Seeding error: {e}")
        return False

def test_ml_predictions():
    """Test ML prediction engine with real data."""
    print("\n" + "="*70)
    print("TESTING ML PREDICTIONS")
    print("="*70)
    
    try:
        db = SessionLocal()
        stocks = db.query(Stock).all()
        
        if not stocks:
            print("❌ No stocks to test")
            db.close()
            return False
        
        stock = stocks[0]
        print(f"Testing with {stock.symbol}...")
        
        # Get price data
        cutoff = datetime.utcnow() - timedelta(days=30)
        prices_db = db.query(PriceHistory).filter(
            PriceHistory.stock_id == stock.id,
            PriceHistory.date >= cutoff
        ).order_by(PriceHistory.date.asc()).all()
        
        if not prices_db:
            print(f"❌ No price data for {stock.symbol}")
            db.close()
            return False
        
        print(f"✅ Found {len(prices_db)} price records")
        
        # Generate prediction
        historical_prices = np.array([float(p.close_price) for p in prices_db])
        historical_dates = [p.date for p in prices_db]
        
        prediction = ml_engine.predict_price(
            historical_prices=historical_prices.tolist(),
            historical_dates=historical_dates,
            stock_symbol=stock.symbol,
            prediction_hours=24
        )
        
        if prediction['status'] == 'success':
            print(f"✅ Prediction generated")
            print(f"  - Recommendation: {prediction.get('recommendation', 'N/A')}")
            print(f"  - RSI: {prediction['technical_analysis']['rsi']:.1f}")
            print(f"  - Volatility: {prediction['technical_analysis']['volatility']:.2f}%")
            print(f"  - Momentum: {prediction['technical_analysis']['momentum']:.2f}%")
            db.close()
            return True
        else:
            print(f"❌ Prediction error: {prediction.get('message', 'Unknown')}")
            db.close()
            return False
            
    except Exception as e:
        print(f"❌ Prediction test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sentiment():
    """Test sentiment analysis."""
    print("\n" + "="*70)
    print("TESTING SENTIMENT ANALYSIS")
    print("="*70)
    
    try:
        db = SessionLocal()
        stocks = db.query(Stock).all()
        
        if not stocks:
            print("❌ No stocks to test")
            db.close()
            return False
        
        stock = stocks[0]
        print(f"Testing with {stock.symbol}...")
        
        sentiment = sentiment_analyzer.get_sentiment_for_stock(stock.symbol)
        
        print(f"✅ Sentiment analysis generated")
        print(f"  - Status: {sentiment.get('status', 'N/A')}")
        print(f"  - Overall Sentiment: {sentiment.get('overall_sentiment', 'N/A')}")
        print(f"  - Sentiment Label: {sentiment.get('sentiment_label', 'N/A')}")
        print(f"  - Positive Articles: {sentiment.get('positive_articles', 0)}")
        print(f"  - Negative Articles: {sentiment.get('negative_articles', 0)}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Sentiment test error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("STOCK PREDICTOR - COMPREHENSIVE FIX & TEST")
    print("="*70)
    
    # Step 1: Check database
    db_ok = check_database()
    
    if not db_ok:
        # Step 2: Seed database
        seed_ok = seed_database()
        if not seed_ok:
            print("\n❌ Failed to seed database")
            return
    
    # Step 3: Test ML predictions
    ml_ok = test_ml_predictions()
    
    # Step 4: Test sentiment
    sent_ok = test_sentiment()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"ML Predictions: {'✅ OK' if ml_ok else '❌ FAILED'}")
    print(f"Sentiment Analysis: {'✅ OK' if sent_ok else '❌ FAILED'}")
    print("="*70)
    
    if ml_ok and sent_ok:
        print("\n✅ All checks passed!")
        print("Backend should be working correctly.")
        print("Refresh frontend at http://localhost:3000")
    else:
        print("\n❌ Some checks failed.")
        print("Review the output above for details.")

if __name__ == "__main__":
    main()
