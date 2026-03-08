#!/usr/bin/env python3
"""
Seed demo user account for testing authentication.
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.base import engine
from app.db.models import User
from app.api.V1.routes.auth import hash_password
from sqlalchemy.orm import sessionmaker

def seed_demo_user():
    """Add demo user to database."""
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if demo user already exists
        existing = session.query(User).filter(User.email == "demo@example.com").first()
        
        if existing:
            print("Demo user already exists: demo@example.com")
            return True
        
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
        
        print("✅ Demo user created successfully!")
        print("\nLogin Credentials:")
        print("  Email: demo@example.com")
        print("  Password: password")
        print("\nYou can now login at http://localhost:3000/login")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating demo user: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("SEEDING DEMO USER ACCOUNT")
    print("=" * 60)
    
    success = seed_demo_user()
    sys.exit(0 if success else 1)
