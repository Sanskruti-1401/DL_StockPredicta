#!/usr/bin/env python3
"""
Reset demo user credentials.
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

def reset_demo_user():
    """Reset demo user with new password hash."""
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find existing demo user
        user = session.query(User).filter(User.email == "demo@example.com").first()
        
        if not user:
            print("Demo user not found. Creating new one...")
            user = User(
                email="demo@example.com",
                username="demo",
                full_name="Demo User",
                hashed_password=hash_password("password"),
                is_active=True,
            )
            session.add(user)
        else:
            print(f"Found existing user: {user.email}")
            print(f"Resetting password...")
            user.hashed_password = hash_password("password")
        
        session.commit()
        print("✅ Demo user ready!")
        print("\nLogin Credentials:")
        print("  Email: demo@example.com")
        print("  Password: password")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("RESETTING DEMO USER")
    print("=" * 60)
    
    success = reset_demo_user()
    sys.exit(0 if success else 1)
