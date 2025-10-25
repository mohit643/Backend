from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Delivery(Base):
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    
    # Delhivery Details
    waybill_number = Column(String(100), unique=True, index=True)
    shipment_id = Column(String(100))
    
    # Tracking Info
    current_status = Column(String(100))
    current_location = Column(String(200))
    
    # Estimated Delivery
    estimated_delivery_date = Column(DateTime(timezone=True))
    actual_delivery_date = Column(DateTime(timezone=True))
    
    # Shipping Details
    courier_name = Column(String(100), default="Delhivery")
    tracking_url = Column(String(500))
    
    # Weight & Dimensions
    weight = Column(Float)  # in kg
    length = Column(Float)  # in cm
    breadth = Column(Float)  # in cm
    height = Column(Float)  # in cm
    
    # Charges
    shipping_charge = Column(Float)
    cod_charge = Column(Float, default=0.0)
    
    # Tracking History (JSON)
    tracking_history = Column(JSON, default=[])
    
    # Timestamps
    picked_up_at = Column(DateTime(timezone=True))
    in_transit_at = Column(DateTime(timezone=True))
    out_for_delivery_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="delivery")
    
    def __repr__(self):
        return f"<Delivery {self.waybill_number}>"