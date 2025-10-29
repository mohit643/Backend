# setup_database.py
from sqlalchemy import create_engine, text
from app.models.customer import Base as CustomerBase
from app.models.order import Base as OrderBase
from app.models.delivery import Base as DeliveryBase

# Supabase DATABASE_URL
DATABASE_URL = "postgresql://postgres:Mohit%4018@db.lrkakuepzkohhrlwaytp.supabase.co:5432/postgres"

try:
    print("🔗 Connecting to Supabase database...")
    engine = create_engine(DATABASE_URL)
    
    # ========== STEP 1: CREATE TABLES ==========
    print("\n📝 Creating tables...")
    CustomerBase.metadata.create_all(engine)
    OrderBase.metadata.create_all(engine)
    DeliveryBase.metadata.create_all(engine)
    print("✅ Tables created!")
    
    # ========== STEP 2: VERIFY TABLES ==========
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📊 Tables in database: {len(tables)}")
    for table in tables:
        print(f"   ✓ {table}")
    
    # ========== STEP 3: ADD is_admin COLUMN ==========
    print("\n📝 Adding is_admin column to customers...")
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE customers 
            ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL
        """))
        conn.commit()
    print("✅ is_admin column added!")
    
    # ========== STEP 4: CREATE ADMIN USER ==========
    print("\n👑 Setting up admin user...")
    
    # First, check if user exists
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, email, full_name FROM customers 
            WHERE email = 'sahumohit643@gmail.com'
        """))
        user = result.fetchone()
        
        if user:
            # User exists, make admin
            conn.execute(text("""
                UPDATE customers 
                SET is_admin = TRUE 
                WHERE email = 'sahumohit643@gmail.com'
            """))
            conn.commit()
            print(f"✅ Made existing user admin: {user[1]}")
        else:
            # User doesn't exist, create admin user
            conn.execute(text("""
                INSERT INTO customers (phone, email, full_name, is_admin)
                VALUES ('918887948909', 'sahumohit643@gmail.com', 'Mohit Sahu', TRUE)
            """))
            conn.commit()
            print("✅ Created new admin user: sahumohit643@gmail.com")
    
    # ========== STEP 5: VERIFY ADMIN ==========
    print("\n🔍 Verifying admin user...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, email, full_name, phone, is_admin, created_at 
            FROM customers 
            WHERE email = 'sahumohit643@gmail.com'
        """))
        admin = result.fetchone()
        
        if admin:
            print(f"\n✅ ADMIN USER:")
            print(f"   ID: {admin[0]}")
            print(f"   Email: {admin[1]}")
            print(f"   Name: {admin[2]}")
            print(f"   Phone: {admin[3]}")
            print(f"   Is Admin: {admin[4]}")
            print(f"   Created: {admin[5]}")
    
    print("\n✅ DATABASE SETUP COMPLETE!")
    print("\n🎉 You can now login at: https://thepureanddesi.com/admin")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()