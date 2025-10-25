from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database.connection import Base

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    COD = "cod"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer Info
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Shipping Address
    shipping_name = Column(String(200), nullable=False)
    shipping_phone = Column(String(15), nullable=False)
    shipping_email = Column(String(200), nullable=False)
    shipping_address = Column(String(500), nullable=False)
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=False)
    shipping_pincode = Column(String(10), nullable=False)
    shipping_landmark = Column(String(200))
    
    # Order Details
    subtotal = Column(Float, nullable=False)
    shipping_cost = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    
    # Payment Info
    payment_method = Column(String(50), nullable=False)  # online, cod
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    razorpay_order_id = Column(String(100))
    razorpay_payment_id = Column(String(100))
    razorpay_signature = Column(String(200))
    
    # Order Status
    order_status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # Delivery Info
    waybill_number = Column(String(100))
    estimated_delivery = Column(String(50))
    delivered_at = Column(DateTime(timezone=True))
    
    # Notes
    customer_notes = Column(Text)
    admin_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery = relationship("Delivery", back_populates="order", uselist=False)
    
    def __repr__(self):
        return f"<Order {self.order_id}>"


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    product_name = Column(String(200), nullable=False)
    product_slug = Column(String(200), nullable=False)
    product_image = Column(String(500), nullable=False)
    
    size = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="items")
    
    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"