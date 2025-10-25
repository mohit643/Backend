# backend/app/schemas/delivery_schema.py (NEW FILE - CREATE THIS)

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class DeliveryPartner(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

class TrackingHistoryEntry(BaseModel):
    status: str
    location: Optional[str] = None
    timestamp: str
    description: Optional[str] = None

class DeliveryBase(BaseModel):
    waybill_number: str
    courier_name: str = "Delhivery"
    current_status: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None

class DeliveryResponse(DeliveryBase):
    id: int
    order_id: int
    tracking_url: Optional[str] = None
    current_location: Optional[str] = None
    picked_up_at: Optional[datetime] = None
    in_transit_at: Optional[datetime] = None
    out_for_delivery_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class DeliveryTrackingResponse(BaseModel):
    success: bool
    order_id: str
    waybill_number: str
    current_status: str
    current_location: Optional[str] = None
    courier_name: str
    tracking_url: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    in_transit_at: Optional[datetime] = None
    out_for_delivery_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    tracking_history: List[Dict] = []

class DeliveryStatusUpdate(BaseModel):
    status: str
    location: Optional[str] = None
    description: Optional[str] = None