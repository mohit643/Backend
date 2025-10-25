from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    
    price = Column(Float, nullable=False)
    mrp = Column(Float, nullable=False)
    discount = Column(Integer, default=0)
    
    size = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False)
    
    image = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=100)
    
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    
    weight = Column(Float, default=1.0)  # in kg for shipping
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product {self.name}>"