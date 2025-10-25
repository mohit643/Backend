import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import create_tables, engine
from app.models import Product, Order, OrderItem, Customer, Delivery

def init_database():
    """Initialize database with tables"""
    try:
        print("🚀 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        return False

if __name__ == "__main__":
    init_database()