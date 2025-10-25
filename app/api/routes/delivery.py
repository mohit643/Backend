# backend/app/api/routes/delivery.py (REPLACE COMPLETE FILE)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import traceback

from app.database.connection import get_db
from app.models.order import Order
from app.models.delivery import Delivery

router = APIRouter(prefix="/delivery", tags=["Delivery"])

# ============================================
# PYDANTIC SCHEMAS (Define Here)
# ============================================

class DeliveryTrackingResponse(BaseModel):
    success: bool
    order_id: str
    waybill_number: str
    current_status: Optional[str] = None
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

class PincodeCheck(BaseModel):
    pincode: str

class ShippingCalculation(BaseModel):
    pincode: str
    weight: float
    cod_amount: Optional[float] = 0

# Metro city pincodes (first 3 digits)
METRO_CITIES = ["110", "400", "560", "600", "700", "500", "122", "201"]

# ============================================
# DELIVERY TRACKING ROUTES
# ============================================

@router.get("/track/{order_id}")
async def track_delivery(order_id: str, db: Session = Depends(get_db)):
    """Track delivery by order ID"""
    try:
        print(f"🔍 Tracking delivery for order: {order_id}")
        
        # Get order
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Get delivery
        delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
        
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery information not available yet"
            )
        
        print(f"✅ Delivery found: {delivery.waybill_number}")
        
        return {
            "success": True,
            "order_id": order.order_id,
            "waybill_number": delivery.waybill_number,
            "current_status": delivery.current_status,
            "current_location": delivery.current_location,
            "courier_name": delivery.courier_name,
            "tracking_url": delivery.tracking_url,
            "estimated_delivery_date": delivery.estimated_delivery_date,
            "picked_up_at": delivery.picked_up_at,
            "in_transit_at": delivery.in_transit_at,
            "out_for_delivery_at": delivery.out_for_delivery_at,
            "delivered_at": delivery.delivered_at,
            "tracking_history": delivery.tracking_history or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error tracking delivery: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track delivery"
        )


@router.get("/track-waybill/{waybill_number}")
async def track_by_waybill(waybill_number: str, db: Session = Depends(get_db)):
    """Track delivery by waybill number"""
    try:
        print(f"🔍 Tracking waybill: {waybill_number}")
        
        delivery = db.query(Delivery).filter(
            Delivery.waybill_number == waybill_number
        ).first()
        
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracking number not found"
            )
        
        order = db.query(Order).filter(Order.id == delivery.order_id).first()
        
        return {
            "success": True,
            "order_id": order.order_id if order else None,
            "waybill_number": delivery.waybill_number,
            "current_status": delivery.current_status,
            "current_location": delivery.current_location,
            "courier_name": delivery.courier_name,
            "tracking_url": delivery.tracking_url,
            "estimated_delivery_date": delivery.estimated_delivery_date,
            "picked_up_at": delivery.picked_up_at,
            "in_transit_at": delivery.in_transit_at,
            "out_for_delivery_at": delivery.out_for_delivery_at,
            "delivered_at": delivery.delivered_at,
            "tracking_history": delivery.tracking_history or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error tracking delivery: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track delivery"
        )


@router.post("/update-status/{waybill_number}")
async def update_delivery_status(
    waybill_number: str,
    status_update: DeliveryStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update delivery status (Admin/Webhook use)"""
    try:
        print(f"📦 Updating delivery status: {waybill_number}")
        
        delivery = db.query(Delivery).filter(
            Delivery.waybill_number == waybill_number
        ).first()
        
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery not found"
            )
        
        # Update status and location
        delivery.current_status = status_update.status
        if status_update.location:
            delivery.current_location = status_update.location
        
        # Update timestamps based on status
        now = datetime.utcnow()
        status_lower = status_update.status.lower()
        
        if "picked" in status_lower or "pickup" in status_lower:
            delivery.picked_up_at = now
        elif "transit" in status_lower:
            delivery.in_transit_at = now
        elif "out for delivery" in status_lower:
            delivery.out_for_delivery_at = now
        elif "delivered" in status_lower:
            delivery.delivered_at = now
            
            # Update order status
            order = db.query(Order).filter(Order.id == delivery.order_id).first()
            if order:
                order.order_status = "DELIVERED"
                order.delivered_at = now
        
        # Add to tracking history
        if not delivery.tracking_history:
            delivery.tracking_history = []
        
        tracking_entry = {
            "status": status_update.status,
            "location": status_update.location or delivery.current_location,
            "timestamp": now.isoformat(),
            "description": status_update.description or f"Package {status_update.status}"
        }
        
        delivery.tracking_history.append(tracking_entry)
        
        db.commit()
        
        print(f"✅ Delivery status updated: {status_update.status}")
        
        return {
            "success": True,
            "message": "Delivery status updated successfully",
            "waybill_number": waybill_number,
            "status": status_update.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating delivery: {str(e)}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update delivery status"
        )


# ============================================
# PINCODE & SHIPPING ROUTES
# ============================================

@router.get("/check-pincode/{pincode}")
async def check_pincode_serviceability(pincode: str):
    """Check if delivery is available for pincode"""
    try:
        # Basic validation
        if len(pincode) != 6 or not pincode.isdigit():
            raise HTTPException(status_code=400, detail="Invalid pincode format")
        
        # Check if metro city
        is_metro = any(pincode.startswith(code) for code in METRO_CITIES)
        
        return {
            "serviceable": True,
            "pincode": pincode,
            "is_metro": is_metro,
            "cod_available": True,
            "prepaid_available": True,
            "estimated_days": 3 if is_metro else 5
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-shipping")
async def calculate_shipping_charges(data: ShippingCalculation):
    """Calculate shipping charges based on pincode and weight"""
    try:
        # Check if metro city
        is_metro = any(data.pincode.startswith(code) for code in METRO_CITIES)
        
        # Base shipping charges
        base_charge = 50 if is_metro else 70
        
        # Weight-based charges (per kg)
        weight_charge = 0
        if data.weight > 1:
            weight_charge = (data.weight - 1) * 20
        
        shipping_charge = base_charge + weight_charge
        
        # COD charges
        cod_charge = 0
        if data.cod_amount > 0:
            cod_charge = 50
        
        total_charge = shipping_charge + cod_charge
        
        return {
            "pincode": data.pincode,
            "is_metro": is_metro,
            "base_charge": base_charge,
            "weight_charge": weight_charge,
            "shipping_charge": shipping_charge,
            "cod_charge": cod_charge,
            "total_charge": total_charge
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estimate/{pincode}")
async def get_estimated_delivery(pincode: str):
    """Get estimated delivery date for pincode"""
    try:
        # Validate pincode
        if len(pincode) != 6 or not pincode.isdigit():
            raise HTTPException(status_code=400, detail="Invalid pincode format")
        
        # Check if metro city
        is_metro = any(pincode.startswith(code) for code in METRO_CITIES)
        
        # Calculate estimated delivery
        delivery_days = 3 if is_metro else 5
        estimated_date = datetime.now() + timedelta(days=delivery_days)
        
        return {
            "pincode": pincode,
            "is_metro": is_metro,
            "estimated_days": delivery_days,
            "estimated_date": estimated_date.strftime("%Y-%m-%d"),
            "estimated_date_formatted": estimated_date.strftime("%d %B, %Y")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))