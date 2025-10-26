# backend/migrate_admin.py (CREATE THIS NEW FILE - Run once)
from sqlalchemy import text
from app.database.connection import engine, SessionLocal

def add_admin_column():
    """Add is_admin column to customers table"""
    with engine.connect() as conn:
        try:
            # Add column
            conn.execute(text("""
                ALTER TABLE customers 
                ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL
            """))
            conn.commit()
            print("✅ Added is_admin column to customers table")
            
            # Make sahumohit643@gmail.com admin
            result = conn.execute(text("""
                UPDATE customers 
                SET is_admin = TRUE 
                WHERE email = 'sahumohit643@gmail.com'
                RETURNING id, email, full_name
            """))
            conn.commit()
            
            admin_user = result.fetchone()
            if admin_user:
                print(f"✅ Made admin: {admin_user[1]} ({admin_user[2]})")
            else:
                print("⚠️  Email sahumohit643@gmail.com not found in database")
                print("   Please login with Google first, then run this script again")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            conn.rollback()

if __name__ == "__main__":
    print("🚀 Starting admin migration...")
    add_admin_column()
    print("✅ Migration complete!")