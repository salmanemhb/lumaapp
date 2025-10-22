"""
Clear all companies from the database
This will DELETE all company records but keep the table structure
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.database import Company


def main():
    print("⚠️  WARNING: This will DELETE all companies from the database!")
    print()
    
    # List current companies
    db = SessionLocal()
    try:
        companies = db.query(Company).all()
        if companies:
            print(f"📋 Current companies ({len(companies)}):")
            for company in companies:
                email = company.contact_email or "No email"
                print(f"  - {company.name} ({email}) - Approved: {company.approved}")
            print()
        else:
            print("📋 No companies found in database")
            print()
            return
        
        confirm = input("Type 'CLEAR' to delete all companies: ")
        
        if confirm != "CLEAR":
            print("❌ Aborted")
            return
        
        print("\n🗑️  Clearing companies...")
        count = db.query(Company).delete()
        db.commit()
        print(f"✅ Deleted {count} companies successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
