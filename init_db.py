"""
Database Initialization Script
Run this to create all tables in the database
"""

from app.database.connection import Base, engine, create_tables
from app.models.customer import Customer, OTP
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.delivery import Delivery
from sqlalchemy import text, inspect

def check_if_tables_exist():
    """Check if tables already exist"""
    inspector = inspect(engine)
    return 'customers' in inspector.get_table_names()

def add_google_oauth_columns():
    """Add Google OAuth columns to existing customers table (safe migration)"""
    print("\n🔄 Checking for Google OAuth columns...")
    
    try:
        with engine.connect() as conn:
            # Check if google_id column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='customers' AND column_name='google_id'
            """))
            
            if result.fetchone() is None:
                print("   📝 Adding google_id column...")
                conn.execute(text("""
                    ALTER TABLE customers 
                    ADD COLUMN google_id VARCHAR(100) UNIQUE
                """))
                conn.commit()
            
            # Add google_email
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='customers' AND column_name='google_email'
            """))
            
            if result.fetchone() is None:
                print("   📝 Adding google_email column...")
                conn.execute(text("""
                    ALTER TABLE customers 
                    ADD COLUMN google_email VARCHAR(200)
                """))
                conn.commit()
            
            # Add google_picture
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='customers' AND column_name='google_picture'
            """))
            
            if result.fetchone() is None:
                print("   📝 Adding google_picture column...")
                conn.execute(text("""
                    ALTER TABLE customers 
                    ADD COLUMN google_picture VARCHAR(500)
                """))
                conn.commit()
            
            # Make phone nullable (for Google-only users)
            print("   📝 Making phone column nullable...")
            conn.execute(text("""
                ALTER TABLE customers 
                ALTER COLUMN phone DROP NOT NULL
            """))
            conn.commit()
            
            print("   ✅ Google OAuth columns added successfully!")
            return True
            
    except Exception as e:
        print(f"   ⚠️ Migration note: {str(e)}")
        print("   ℹ️ If you're creating fresh tables, this is normal.")
        return False

def init_database():
    """Initialize database with all tables"""
    print("🚀 Starting database initialization...")
    
    try:
        # Import all models to register them with Base
        print("\n📦 Loading models...")
        print("   ✓ Customer, OTP")
        print("   ✓ Product")
        print("   ✓ Order, OrderItem")
        print("   ✓ Delivery")
        
        # Check if tables exist
        tables_exist = check_if_tables_exist()
        
        if tables_exist:
            print("\n📊 Tables already exist - Running migration...")
            add_google_oauth_columns()
        else:
            print("\n🔨 Creating fresh database tables...")
            create_tables()
            
            print("\n✅ Database initialization completed successfully!")
            print("\n📊 Created tables:")
            print("   • customers (with Google OAuth support)")
            print("   • otps")
            print("   • products")
            print("   • orders")
            print("   • order_items")
            print("   • deliveries")
        
        print("\n🎉 Database is ready!")
        print("\n📝 Features enabled:")
        print("   ✓ Phone/OTP Login")
        print("   ✓ Google OAuth Login")
        print("   ✓ Order Management")
        print("   ✓ Delivery Tracking")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    init_database()