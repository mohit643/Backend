# backend/app/schemas/product_schema.py (NEW FILE - CREATE THIS)

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    slug: str
    category: str
    price: float
    mrp: float
    discount: int
    size: str
    unit: str
    description: str
    image: str

class ProductCreate(ProductBase):
    images: Optional[str] = None
    in_stock: bool = True
    stock_quantity: int = 0

class Product(ProductBase):
    id: int
    images: Optional[str] = None
    in_stock: bool
    stock_quantity: int
    rating: float
    reviews: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    category: str
    price: float
    mrp: float
    discount: int
    size: str
    unit: str
    description: str
    image: str
    images: Optional[str] = None
    in_stock: bool
    stock_quantity: int
    rating: float
    reviews: int
    
    class Config:
        from_attributes = True