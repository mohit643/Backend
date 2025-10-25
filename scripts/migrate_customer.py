import sys
sys.path.append('.')

from sqlalchemy import text
from app.database.connection import engine, Base
from app.models import Customer, OTP

def migrate_customer_table():
    """Add new columns to existing customers table"""
    try:
        with engine.connect() as conn:
            # Add last_login column if not exists
            try:
                conn.execute(text("""
                    ALTER TABLE customers 
                    ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE
                """))
                print("✅ Added last_login column")
            except Exception as e:
                print(f"⚠️ last_login column: {e}")
            
            # Make email nullable
            try:
                conn.execute(text("""
                    ALTER TABLE customers 
                    ALTER COLUMN email DROP NOT NULL
                """))
                print("✅ Made email nullable")
            except Exception as e:
                print(f"⚠️ email nullable: {e}")
            
            # Make full_name nullable
            try:
                conn.execute(text("""
                    ALTER TABLE customers 
                    ALTER COLUMN full_name DROP NOT NULL
                """))
                print("✅ Made full_name nullable")
            except Exception as e:
                print(f"⚠️ full_name nullable: {e}")
            
            conn.commit()
        
        print("\n✅ Customer table migration completed!")
        
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")

def create_otp_table():
    """Create OTP table"""
    try:
        # Create OTP table
        Base.metadata.tables['otps'].create(engine, checkfirst=True)
        print("✅ OTP table created successfully!")
        
    except Exception as e:
        print(f"❌ OTP table error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting database migration...\n")
    migrate_customer_table()
    create_otp_table()
    print("\n🎉 Migration completed!")