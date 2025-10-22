"""
Check user credentials in database
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.database import User, Company
from app.services.auth import verify_password


def check_user(email: str, password: str = None):
    """Check if user exists and optionally verify password"""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User not found: {email}")
            print("\nAvailable users:")
            all_users = db.query(User).all()
            for u in all_users:
                print(f"  - {u.email} (approved: {u.approved})")
            return
        
        print(f"✅ User found: {email}")
        print(f"  ID: {user.id}")
        print(f"  Company ID: {user.company_id}")
        print(f"  Approved: {user.approved}")
        print(f"  Role: {user.role.value}")
        print(f"  Password hash: {user.password_hash[:50]}...")
        
        # Check company
        company = db.query(Company).filter(Company.id == user.company_id).first()
        if company:
            print(f"\n✅ Company found: {company.name}")
            print(f"  Approved: {company.approved}")
        else:
            print(f"\n❌ Company not found for ID: {user.company_id}")
        
        # Verify password if provided
        if password:
            print(f"\n🔐 Testing password...")
            try:
                is_valid = verify_password(password, user.password_hash)
                if is_valid:
                    print(f"✅ Password is correct!")
                else:
                    print(f"❌ Password is incorrect!")
            except Exception as e:
                print(f"❌ Error verifying password: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_user.py <email> [password]")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    
    check_user(email, password)
