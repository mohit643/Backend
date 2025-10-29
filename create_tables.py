# create_tables.py
from sqlalchemy import create_engine
from app.models.customer import Base as CustomerBase
from app.models.order import Base as OrderBase
from app.models.delivery import Base as DeliveryBase

# Supabase DATABASE_URL
DATABASE_URL = "postgresql://postgres:Mohit%4018@db.lrkakuepzkohhrlwaytp.supabase.co:5432/postgres"

try:
    print("🔗 Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    print("📝 Creating tables...")
    
    # Create all tables
    CustomerBase.metadata.create_all(engine)
    OrderBase.metadata.create_all(engine)
    DeliveryBase.metadata.create_all(engine)
    
    print("✅ All tables created successfully!")
    
    # Verify tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📊 Tables in database: {len(tables)}")
    for table in tables:
        print(f"   ✓ {table}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()