# backend/app/models/__init__.py
from app.database.connection import Base

# Import all models
from .product import Product
from .customer import Customer, OTP
from .order import Order, OrderItem, OrderStatus, PaymentStatus
from .delivery import Delivery

__all__ = [
    "Base",
    "Product",
    "Customer",
    "OTP",
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentStatus",
    "Delivery"
]