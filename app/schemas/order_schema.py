# backend/app/schemas/order_schema.py (COMPLETE FILE)

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# ============================================
# SHIPPING ADDRESS SCHEMA
# ============================================

class ShippingAddress(BaseModel):
    fullName: str
    phone: str
    email: EmailStr
    address: str
    city: str
    state: str
    pincode: str
    landmark: Optional[str] = ""

# ============================================
# ORDER ITEM SCHEMA
# ============================================

class OrderItemCreate(BaseModel):
    productId: int
    productName: str
    quantity: int
    price: float
    size: str
    unit: str

class OrderItemResponse(BaseModel):
    id: int
    productName: str
    quantity: int
    price: float
    size: str
    unit: str
    total: float
    
    class Config:
        from_attributes = True

# ============================================
# ORDER CREATE SCHEMA
# ============================================

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    shippingAddress: ShippingAddress
    paymentMethod: str  # "online" or "cod"

# ============================================
# ORDER RESPONSE SCHEMA
# ============================================

class OrderResponse(BaseModel):
    success: bool
    message: str
    orderId: str
    total: float

class OrderDetailResponse(BaseModel):
    orderId: str
    customerId: int
    customerName: str
    
    # Shipping Details
    shippingName: str
    shippingPhone: str
    shippingEmail: str
    shippingAddress: str
    shippingCity: str
    shippingState: str
    shippingPincode: str
    
    # Order Details
    subtotal: float
    shippingCost: float
    discount: float
    tax: float
    total: float
    
    # Payment Info
    paymentMethod: str
    paymentStatus: str
    
    # Order Status
    orderStatus: str
    
    # Delivery Info
    waybillNumber: Optional[str] = None
    estimatedDelivery: Optional[str] = None
    
    # Items
    items: List[OrderItemResponse]
    
    # Timestamps
    createdAt: datetime
    
    class Config:
        from_attributes = True

# ============================================
# ORDER LIST SCHEMA
# ============================================

class OrderListItem(BaseModel):
    orderId: str
    customerName: str
    total: float
    paymentMethod: str
    paymentStatus: str
    orderStatus: str
    createdAt: datetime
    itemCount: int
    
    class Config:
        from_attributes = True

# ============================================
# ORDER STATUS UPDATE
# ============================================

class OrderStatusUpdate(BaseModel):
    status: str  # pending, confirmed, processing, shipped, delivered, cancelled

class OrderCancelRequest(BaseModel):
    reason: Optional[str] = None