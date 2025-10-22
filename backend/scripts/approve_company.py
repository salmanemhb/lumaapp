"""
Company approval script
Usage: python approve_company.py <company_name> <user_email> [password]
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.database import Company, User, UserRole
from app.services.auth import hash_password, generate_random_password
from app.services.email import EmailService


def approve_company(company_name: str, user_email: str, password: str = None):
    """
    Approve a company and create user credentials
    
    Args:
        company_name: Name of the company to approve
        user_email: Email for the user account
        password: Optional password (will be auto-generated if not provided)
    """
    db: Session = SessionLocal()
    
    try:
        # Find company
        company = db.query(Company).filter(Company.name == company_name).first()
        
        if not company:
            print(f"❌ Error: Company '{company_name}' not found")
            print("Available pending companies:")
            pending = db.query(Company).filter(Company.approved == False).all()
            for c in pending:
                print(f"  - {c.name} ({c.contact_email})")
            return
        
        if company.approved:
            print(f"⚠️  Company '{company_name}' is already approved")
            return
        
        # Generate password if not provided (bcrypt max is 72 bytes)
        if not password:
            password = generate_random_password(length=12)  # Shorter to avoid bcrypt limit
            print(f"🔑 Generated password: {password}")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_email).first()
        if existing_user:
            print(f"❌ Error: User with email '{user_email}' already exists")
            return
        
        # Approve company
        company.approved = True
        
        # Create user
        user = User(
            company_id=company.id,
            email=user_email,
            password_hash=hash_password(password),
            approved=True,
            role=UserRole.COMPANY
        )
        
        db.add(user)
        db.commit()
        db.refresh(company)
        db.refresh(user)
        
        print(f"✅ Company '{company_name}' approved successfully")
        print(f"✅ User created: {user_email}")
        
        # Send credentials email
        try:
            EmailService.send_credentials_email(
                to_email=company.contact_email or user_email,
                company_name=company.name,
                user_email=user_email,
                password=password,
                language="es"  # Default to Spanish
            )
            print(f"📧 Credentials email sent to {company.contact_email or user_email}")
        except Exception as e:
            print(f"⚠️  Failed to send email: {e}")
            print(f"⚠️  Please manually send credentials to user:")
            print(f"   Email: {user_email}")
            print(f"   Password: {password}")
        
        print("\n🎉 Approval complete!")
        print(f"Company: {company.name}")
        print(f"User Email: {user_email}")
        print(f"Password: {password}")
        print(f"Login URL: https://getluma.es/login")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def list_pending_companies():
    """List all pending companies"""
    db: Session = SessionLocal()
    
    try:
        pending = db.query(Company).filter(Company.approved == False).all()
        
        if not pending:
            print("No pending companies")
            return
        
        print("\n📋 Pending Companies:")
        print("-" * 60)
        for company in pending:
            print(f"Name: {company.name}")
            print(f"Contact: {company.contact_email}")
            print(f"Sector: {company.sector or 'N/A'}")
            print(f"Registered: {company.created_at.strftime('%Y-%m-%d %H:%M')}")
            print("-" * 60)
    
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Luma Company Approval Tool\n")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python approve_company.py <company_name> <user_email> [password]")
        print("  python approve_company.py --list")
        print("\nExamples:")
        print("  python approve_company.py 'Acme Corp' admin@acmecorp.es")
        print("  python approve_company.py 'Acme Corp' admin@acmecorp.es MySecurePass123")
        print("  python approve_company.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_pending_companies()
    else:
        company_name = sys.argv[1]
        user_email = sys.argv[2] if len(sys.argv) > 2 else None
        password = sys.argv[3] if len(sys.argv) > 3 else None
        
        if not user_email:
            print("❌ Error: user_email is required")
            sys.exit(1)
        
        approve_company(company_name, user_email, password)
