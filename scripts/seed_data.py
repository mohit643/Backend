import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models import Product

def seed_products():
    """Add initial products to database"""
    db = SessionLocal()
    
    try:
        # Check if products already exist
        existing = db.query(Product).first()
        if existing:
            print("⚠️  Products already exist in database!")
            return
        
        products = [
            {
                "name": "Premium Black Mustard Oil (Kachi Ghani)",
                "slug": "black-mustard-oil",
                "category": "Mustard Oil",
                "price": 399.0,
                "mrp": 499.0,
                "discount": 20,
                "size": "1",
                "unit": "Liter",
                "image": "/images/products/blackmustardoil.jpg",
                "description": "Pure cold-pressed black mustard oil extracted using traditional wooden Ghani method. Rich in omega-3 fatty acids and antioxidants.",
                "in_stock": True,
                "stock_quantity": 100,
                "rating": 4.8,
                "reviews_count": 234,
                "weight": 1.0
            },
            {
                "name": "Yellow Mustard Oil (Kachi Ghani)",
                "slug": "yellow-mustard-oil",
                "category": "Mustard Oil",
                "price": 379.0,
                "mrp": 479.0,
                "discount": 21,
                "size": "1",
                "unit": "Liter",
                "image": "/images/products/yellow-mustard-oil.jpg",
                "description": "Cold-pressed yellow mustard oil with mild flavor. Perfect for cooking and traditional remedies.",
                "in_stock": True,
                "stock_quantity": 100,
                "rating": 4.7,
                "reviews_count": 189,
                "weight": 1.0
            },
            {
                "name": "Pure Groundnut Oil (Kachi Ghani)",
                "slug": "groundnut-oil",
                "category": "Groundnut Oil",
                "price": 349.0,
                "mrp": 449.0,
                "discount": 22,
                "size": "1",
                "unit": "Liter",
                "image": "/images/products/groundnut-oil.jpg",
                "description": "Traditional cold-pressed groundnut oil with rich aroma. High smoke point, ideal for deep frying.",
                "in_stock": True,
                "stock_quantity": 100,
                "rating": 4.9,
                "reviews_count": 312,
                "weight": 1.0
            },
            {
                "name": "Pure Sesame Oil (Kachi Ghani)",
                "slug": "sesame-oil",
                "category": "Sesame Oil",
                "price": 429.0,
                "mrp": 549.0,
                "discount": 22,
                "size": "500",
                "unit": "ml",
                "image": "/images/products/sesame-oil.jpg",
                "description": "Premium cold-pressed sesame oil with nutty flavor. Rich in antioxidants and vitamins.",
                "in_stock": True,
                "stock_quantity": 100,
                "rating": 4.6,
                "reviews_count": 156,
                "weight": 0.5
            },
            {
                "name": "Virgin Coconut Oil (Cold-Pressed)",
                "slug": "coconut-oil",
                "category": "Coconut Oil",
                "price": 389.0,
                "mrp": 489.0,
                "discount": 20,
                "size": "500",
                "unit": "ml",
                "image": "/images/products/coconut-oil.jpg",
                "description": "Extra virgin coconut oil extracted from fresh coconuts. Perfect for cooking and hair care.",
                "in_stock": True,
                "stock_quantity": 100,
                "rating": 4.8,
                "reviews_count": 278,
                "weight": 0.5
            }
        ]
        
        print("🌱 Seeding products...")
        
        for product_data in products:
            product = Product(**product_data)
            db.add(product)
        
        db.commit()
        print(f"✅ Successfully added {len(products)} products!")
        
    except Exception as e:
        print(f"❌ Error seeding data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_products() 