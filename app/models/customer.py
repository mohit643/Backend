from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication - Multiple methods
    phone = Column(String(15), unique=True, nullable=True, index=True)  # ✅ Changed to nullable
    email = Column(String(200), unique=True, nullable=True, index=True)
    
    # ✅ NEW: Google OAuth Fields
    google_id = Column(String(100), unique=True, nullable=True, index=True)
    google_email = Column(String(200), nullable=True)
    google_picture = Column(String(500), nullable=True)
    
    # Profile
    full_name = Column(String(200), nullable=True)
    
    # Address fields
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10), index=True)
    landmark = Column(String(200))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    orders = relationship("Order", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer {self.email or self.phone or self.google_id}>"


# OTP Storage Model (No changes needed)
class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), nullable=False, index=True)
    otp = Column(String(6), nullable=False)
    
    purpose = Column(String(50), default="login")
    
    is_used = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    def __repr__(self):
        return f"<OTP {self.phone}>"