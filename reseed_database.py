#!/usr/bin/env python3
"""
Reseed database with 90 days of historical data.
Run this AFTER updating seed.py to use days=90
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.base import Base, engine
from app.db.models import Stock, User
from app.api.V1.routes.seed import generate_price_history
from app.api.V1.routes.auth import hash_password
from app.core.config import settings
from sqlalchemy.orm import sessionmaker

# Database setup
DB_PATH = backend_path / "test.db"

def reseed_database():
    """Delete old database and create new one with 90 days of data"""
    
    print(f"Using database: {settings.DATABASE_URL}")
    
    # Only delete SQLite file for SQLite databases
    if settings.DATABASE_URL.startswith("sqlite"):
        print("Step 1: Deleting old SQLite database...")
        if DB_PATH.exists():
            DB_PATH.unlink()
            print(f"  ✅ Deleted {DB_PATH}")
        else:
            print(f"  ℹ️  No existing database file found")
    else:
        print("Step 1: Skipping database file deletion (using remote database)")
    
    print("\nStep 2: Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("  ✅ Database tables created")
    except Exception as e:
        print(f"  ❌ Error creating tables: {e}")
        raise
    
    print("\nStep 2.5: Seeding demo user account...")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create demo user
        demo_user = User(
            email="demo@example.com",
            username="demo",
            full_name="Demo User",
            hashed_password=hash_password("password"),
            is_active=True,
        )
        session.add(demo_user)
        session.commit()
        print("  ✅ Demo user created: demo@example.com / password")
    except Exception as e:
        session.rollback()
        print(f"  ⚠️  Demo user already exists or error: {e}")
    finally:
        session.close()
    
    print("\nStep 3: Seeding stocks with 90 days of historical data...")
    
    SEED_STOCKS = [
        {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "pe_ratio": 28.5},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "pe_ratio": 32.1},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "pe_ratio": 24.3},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "pe_ratio": 45.2},
        {"symbol": "TSLA", "name": "Tesla, Inc.", "sector": "Automotive", "pe_ratio": 52.1},
        {"symbol": "AMZN", "name": "Amazon.com, Inc.", "sector": "Consumer", "pe_ratio": 38.5},
        {"symbol": "META", "name": "Meta Platforms, Inc.", "sector": "Technology", "pe_ratio": 20.3},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Finance", "pe_ratio": 11.2},
        {"symbol": "V", "name": "Visa Inc.", "sector": "Finance", "pe_ratio": 42.8},
        {"symbol": "UNH", "name": "UnitedHealth Group", "sector": "Healthcare", "pe_ratio": 28.9},
    ]
    
    session2 = Session()
    
    try:
        seeded_count = 0
        total_records = 0
        
        for stock_data in SEED_STOCKS:
            try:
                stock = Stock(**stock_data)
                session2.add(stock)
                session2.commit()
                session2.refresh(stock)
                
                # Generate 90 days of historical data + hourly
                price_history = generate_price_history(stock.id, stock.symbol, days=90)
                
                for price_record in price_history:
                    session2.add(price_record)
                session2.commit()
                
                num_records = len(price_history)
                total_records += num_records
                seeded_count += 1
                print(f"  ✅ {stock.symbol}: {num_records} price records")
                
            except Exception as e:
                session2.rollback()
                print(f"  ❌ Error seeding {stock_data['symbol']}: {e}")
                continue
        
        print(f"\nStep 4: Verification")
        print(f"  ✅ Seeded {seeded_count} stocks")
        print(f"  ✅ Created {total_records} price records (~{int(total_records/seeded_count) if seeded_count > 0 else 0} per stock)")
        
        # Verify data
        stock_count = session2.query(Stock).count()
        print(f"\nStep 5: Database Statistics")
        print(f"  ✅ Total stocks in database: {stock_count}")
        
        return True
        
    finally:
        session2.close()

if __name__ == "__main__":
    print("=" * 60)
    print("STOCKPREDICTOR DATABASE RESEED")
    print("=" * 60)
    
    try:
        success = reseed_database()
        if success:
            print("\n" + "=" * 60)
            print("✅ RESEED COMPLETE!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Restart the backend: python -m uvicorn app.main:app --reload")
            print("2. Refresh the frontend: http://localhost:3000")
            print("3. Check dashboard for real data (RSI, Volatility, Sentiment)")
            print("=" * 60)
    except Exception as e:
        print(f"\n❌ Reseed failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
