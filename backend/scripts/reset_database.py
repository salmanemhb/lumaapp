"""
Reset database schema in Supabase
This will DROP all tables and recreate them with the correct schema
WARNING: This will delete all existing data!
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import reset_db, init_db


def main():
    print("⚠️  WARNING: This will DELETE all existing data in your database!")
    print("⚠️  This includes all companies, users, uploads, reports, etc.")
    print()
    
    confirm = input("Type 'RESET' to confirm: ")
    
    if confirm != "RESET":
        print("❌ Aborted")
        return
    
    print("\n🔄 Resetting database...")
    try:
        reset_db()
        print("✅ Database reset successfully!")
        print("\n📊 Tables created:")
        print("  - companies")
        print("  - users")
        print("  - uploads")
        print("  - reports")
        print("  - compliance_metrics")
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
