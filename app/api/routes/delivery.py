# backend/app/api/routes/delivery.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import traceback

from app.database.connection import get_db
from app.models.order import Order
from app.models.delivery import Delivery
from app.services.shiprocket_service import shiprocket_service

# ✅ PREFIX ADDED HERE
router = APIRouter(prefix="/delivery", tags=["Delivery"])

# ============================================
# PYDANTIC SCHEMAS
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

# ============================================
# PINCODE & SHIPPING ROUTES (SHIPROCKET)
# ============================================

# backend/app/api/routes/delivery.py

@router.get("/check-pincode/{pincode}")
async def check_pincode_serviceability(pincode: str):
    """Check if Shiprocket delivery is available for pincode"""
    try:
        print(f"\n{'='*60}")
        print(f"🔍 PINCODE CHECK API CALLED")
        print(f"📍 Pincode: {pincode}")
        print(f"{'='*60}\n")
        
        # Basic validation
        if len(pincode) != 6 or not pincode.isdigit():
            print(f"❌ Invalid pincode format: {pincode}")
            raise HTTPException(status_code=400, detail="Invalid pincode format")
        
        # Check serviceability via Shiprocket
        print(f"📡 Calling Shiprocket service...")
        result = shiprocket_service.check_pincode_serviceability(pincode)
        
        print(f"✅ Shiprocket response: {result}")
        
        # ✅ ENSURE CITY AND STATE ARE PRESENT
        response = {
            "serviceable": result.get("serviceable", True),
            "pincode": pincode,
            "city": result.get("city", ""),  # Will be filled by mock or real API
            "state": result.get("state", ""),  # Will be filled by mock or real API
            "cod_available": result.get("cod_available", True),
            "prepaid_available": True,
            "estimated_days": result.get("estimated_days", "3-5 days"),
            "shipping_charge": result.get("shipping_charge", 50),
            "courier_name": result.get("courier_name", "Shiprocket")
        }
        
        # ✅ FALLBACK: If still unknown, use basic inference
        if not response["city"] or response["city"] == "Unknown":
            # Try to infer from pincode prefix
            prefix = pincode[:3]
            fallback_map = {
                "110": {"city": "Delhi", "state": "Delhi"},
                "212": {"city": "Jhansi", "state": "Uttar Pradesh"},
                "400": {"city": "Mumbai", "state": "Maharashtra"},
            }
            if prefix in fallback_map:
                response["city"] = fallback_map[prefix]["city"]
                response["state"] = fallback_map[prefix]["state"]
        
        print(f"📤 Final response: {response}\n")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error checking pincode: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-shipping")
async def calculate_shipping_charges(data: ShippingCalculation):
    """Calculate Shiprocket shipping charges based on pincode and weight"""
    try:
        print(f"\n{'='*60}")
        print(f"📦 SHIPPING CALCULATION API CALLED")
        print(f"📍 Pincode: {data.pincode}")
        print(f"⚖️  Weight: {data.weight}kg")
        print(f"💰 COD Amount: ₹{data.cod_amount}")
        print(f"{'='*60}\n")
        
        # Calculate via Shiprocket
        result = shiprocket_service.calculate_shipping_charges(
            data.pincode,
            data.weight,
            data.cod_amount
        )
        
        print(f"✅ Calculation result: {result}")
        
        # ✅ FIXED: Match field names with shiprocket response
        response = {
            "success": True,
            "pincode": data.pincode,
            "weight": data.weight,
            "shipping_charge": result.get("freight_charge", 50),  # ✅ Changed
            "cod_charge": result.get("cod_charges", 0),  # ✅ Changed
            "total_charge": result.get("total_charge", 50),
            "estimated_days": result.get("estimated_delivery_days", "3-5 days")  # ✅ Changed
        }
        
        print(f"📤 Sending response: {response}\n")
        return response
    
    except Exception as e:
        print(f"❌ Error calculating shipping: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estimate/{pincode}")
async def get_estimated_delivery(pincode: str):
    """Get estimated delivery date for pincode via Shiprocket"""
    try:
        print(f"📅 Getting delivery estimate for pincode: {pincode}")
        
        # Validate pincode
        if len(pincode) != 6 or not pincode.isdigit():
            raise HTTPException(status_code=400, detail="Invalid pincode format")
        
        # Check serviceability
        result = shiprocket_service.check_pincode_serviceability(pincode)
        
        # Calculate estimated date
        estimated_days_str = result.get("estimated_days", "3-5 days")
        # Parse "3-5 days" to get max days
        try:
            max_days = int(estimated_days_str.split("-")[1].split()[0])
        except:
            max_days = 5
        
        estimated_date = datetime.now() + timedelta(days=max_days)
        
        return {
            "pincode": pincode,
            "serviceable": result.get("serviceable", True),
            "estimated_days": estimated_days_str,
            "estimated_date": estimated_date.strftime("%Y-%m-%d"),
            "estimated_date_formatted": estimated_date.strftime("%d %B, %Y"),
            "courier_name": result.get("courier_name", "Shiprocket")
        }
    
    except Exception as e:
        print(f"❌ Error getting estimate: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # Get live tracking from Shiprocket if shipment_id exists
        live_tracking = None
        if delivery.shipment_id:
            try:
                live_tracking = shiprocket_service.track_shipment(delivery.shipment_id)
            except Exception as tracking_error:
                print(f"⚠️ Live tracking failed: {str(tracking_error)}")
        
        print(f"✅ Delivery found: {delivery.waybill_number}")
        
        return {
            "success": True,
            "order_id": order.order_id,
            "waybill_number": delivery.waybill_number,
            "shipment_id": delivery.shipment_id,
            "current_status": delivery.current_status,
            "current_location": delivery.current_location,
            "courier_name": delivery.courier_name,
            "tracking_url": delivery.tracking_url,
            "estimated_delivery_date": delivery.estimated_delivery_date,
            "picked_up_at": delivery.picked_up_at,
            "in_transit_at": delivery.in_transit_at,
            "out_for_delivery_at": delivery.out_for_delivery_at,
            "delivered_at": delivery.delivered_at,
            "tracking_history": delivery.tracking_history or [],
            "live_tracking": live_tracking if live_tracking else None
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
        
        # Get live tracking
        live_tracking = None
        if delivery.shipment_id:
            try:
                live_tracking = shiprocket_service.track_shipment(delivery.shipment_id)
            except Exception:
                pass
        
        return {
            "success": True,
            "order_id": order.order_id if order else None,
            "waybill_number": delivery.waybill_number,
            "shipment_id": delivery.shipment_id,
            "current_status": delivery.current_status,
            "current_location": delivery.current_location,
            "courier_name": delivery.courier_name,
            "tracking_url": delivery.tracking_url,
            "estimated_delivery_date": delivery.estimated_delivery_date,
            "picked_up_at": delivery.picked_up_at,
            "in_transit_at": delivery.in_transit_at,
            "out_for_delivery_at": delivery.out_for_delivery_at,
            "delivered_at": delivery.delivered_at,
            "tracking_history": delivery.tracking_history or [],
            "live_tracking": live_tracking if live_tracking else None
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
                from app.models.order import OrderStatus
                order.order_status = OrderStatus.DELIVERED
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