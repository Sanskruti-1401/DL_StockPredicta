#!/usr/bin/env python3
"""
Verify demo user in database.
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.base import engine
from app.db.models import User
from app.api.V1.routes.auth import verify_password, hash_password
from sqlalchemy.orm import sessionmaker

def verify_user():
    """Verify demo user credentials."""
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find demo user
        user = session.query(User).filter(User.email == "demo@example.com").first()
        
        if not user:
            print("❌ Demo user NOT found in database!")
            print("\nAll users in database:")
            all_users = session.query(User).all()
            for u in all_users:
                print(f"  - {u.email} (id={u.id}, active={u.is_active})")
            return False
        
        print(f"✅ User found: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Active: {user.is_active}")
        print(f"   Hashed password: {user.hashed_password[:20]}...")
        
        # Test password verification
        test_password = "password"
        is_valid = verify_password(test_password, user.hashed_password)
        print(f"\n   Testing password 'password': {is_valid}")
        
        if not is_valid:
            print("\n   Password verification FAILED!")
            print("   Re-hashing password...")
            user.hashed_password = hash_password(test_password)
            session.commit()
            print("   ✅ Password re-hashed and saved")
            
            # Verify again
            is_valid = verify_password(test_password, user.hashed_password)
            print(f"   Testing again: {is_valid}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("VERIFYING DEMO USER")
    print("=" * 60 + "\n")
    
    success = verify_user()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Login should work now!")
        print("Email: demo@example.com")
        print("Password: password")
    else:
        print("❌ Something is wrong with the user")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
