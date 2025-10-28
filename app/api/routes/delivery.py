from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import traceback

from app.database.connection import get_db
from app.models.order import Order, OrderStatus
from app.models.delivery import Delivery
from app.services.shiprocket_service import shiprocket_service

router = APIRouter(prefix="/delivery", tags=["Delivery"])

# ==================== MODELS ====================
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


# 🎯 EK HI UNIVERSAL FUNCTION - SAB DELIVERY OPERATIONS HANDLE KAREGA
def handle_delivery_request(
    action: str,
    pincode: Optional[str] = None,
    weight: Optional[float] = None,
    cod_amount: Optional[float] = 0,
    order_id: Optional[str] = None,
    waybill_number: Optional[str] = None,
    status_update: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Universal handler for all delivery operations
    
    Actions:
    - 'check_pincode': Check pincode serviceability
    - 'calculate_shipping': Calculate shipping charges
    - 'estimate_delivery': Get estimated delivery date
    - 'track_order': Track by order ID
    - 'track_waybill': Track by waybill number
    - 'update_status': Update delivery status
    """
    try:
        # ✅ CHECK PINCODE SERVICEABILITY
        if action == "check_pincode":
            print(f"\n{'='*60}")
            print(f"🔍 PINCODE CHECK API CALLED")
            print(f"📍 Pincode: {pincode}")
            print(f"{'='*60}\n")
            
            # Validation
            if not pincode or len(pincode) != 6 or not pincode.isdigit():
                print(f"❌ Invalid pincode format: {pincode}")
                raise HTTPException(status_code=400, detail="Invalid pincode format")
            
            # Check serviceability via Shiprocket
            print(f"📡 Calling Shiprocket service...")
            result = shiprocket_service.check_pincode_serviceability(pincode)
            
            print(f"✅ Shiprocket response: {result}")
            
            response = {
                "serviceable": result.get("serviceable", True),
                "pincode": pincode,
                "city": result.get("city", ""),
                "state": result.get("state", ""),
                "cod_available": result.get("cod_available", True),
                "prepaid_available": True,
                "estimated_days": result.get("estimated_days", "3-5 days"),
                "shipping_charge": result.get("shipping_charge", 50),
                "courier_name": result.get("courier_name", "Shiprocket")
            }
            
            print(f"📤 Final response: {response}\n")
            return response
        
        # ✅ CALCULATE SHIPPING CHARGES
        elif action == "calculate_shipping":
            print(f"\n{'='*60}")
            print(f"📦 SHIPPING CALCULATION API CALLED")
            print(f"📍 Pincode: {pincode}")
            print(f"⚖️  Weight: {weight}kg")
            print(f"💰 COD Amount: ₹{cod_amount}")
            print(f"{'='*60}\n")
            
            if not pincode or not weight:
                raise HTTPException(status_code=400, detail="Pincode and weight required")
            
            # Calculate via Shiprocket
            result = shiprocket_service.calculate_shipping_charges(
                pincode, weight, cod_amount
            )
            
            print(f"✅ Calculation result: {result}")
            
            response = {
                "success": True,
                "pincode": pincode,
                "weight": weight,
                "shipping_charge": result.get("shipping_charge", 50),
                "cod_charge": result.get("cod_charge", 0),
                "total_charge": result.get("total_charge", 50),
                "estimated_days": result.get("estimated_days", "3-5 days")
            }
            
            print(f"📤 Sending response: {response}\n")
            return response
        
        # ✅ ESTIMATE DELIVERY DATE
        elif action == "estimate_delivery":
            print(f"📅 Getting delivery estimate for pincode: {pincode}")
            
            # Validate pincode
            if not pincode or len(pincode) != 6 or not pincode.isdigit():
                raise HTTPException(status_code=400, detail="Invalid pincode format")
            
            # Check serviceability
            result = shiprocket_service.check_pincode_serviceability(pincode)
            
            # Calculate estimated date
            estimated_days_str = result.get("estimated_days", "3-5 days")
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
        
        # ✅ TRACK BY ORDER ID
        elif action == "track_order":
            print(f"🔍 Tracking delivery for order: {order_id}")
            
            if not order_id or not db:
                raise HTTPException(status_code=400, detail="Order ID and DB required")
            
            # Get order
            order = db.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Get delivery
            delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
            if not delivery:
                raise HTTPException(status_code=404, detail="Delivery information not available yet")
            
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
                "live_tracking": live_tracking
            }
        
        # ✅ TRACK BY WAYBILL
        elif action == "track_waybill":
            print(f"🔍 Tracking waybill: {waybill_number}")
            
            if not waybill_number or not db:
                raise HTTPException(status_code=400, detail="Waybill and DB required")
            
            delivery = db.query(Delivery).filter(
                Delivery.waybill_number == waybill_number
            ).first()
            
            if not delivery:
                raise HTTPException(status_code=404, detail="Tracking number not found")
            
            order = db.query(Order).filter(Order.id == delivery.order_id).first()
            
            # Get live tracking
            live_tracking = None
            if delivery.shipment_id:
                try:
                    live_tracking = shiprocket_service.track_shipment(delivery.shipment_id)
                except:
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
                "live_tracking": live_tracking
            }
        
        # ✅ UPDATE DELIVERY STATUS
        elif action == "update_status":
            print(f"📦 Updating delivery status: {waybill_number}")
            
            if not waybill_number or not status_update or not db:
                raise HTTPException(status_code=400, detail="Required data missing")
            
            delivery = db.query(Delivery).filter(
                Delivery.waybill_number == waybill_number
            ).first()
            
            if not delivery:
                raise HTTPException(status_code=404, detail="Delivery not found")
            
            # Update status and location
            delivery.current_status = status_update["status"]
            if status_update.get("location"):
                delivery.current_location = status_update["location"]
            
            # Update timestamps based on status
            now = datetime.utcnow()
            status_lower = status_update["status"].lower()
            
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
                    order.order_status = OrderStatus.DELIVERED
                    order.delivered_at = now
            
            # Add to tracking history
            if not delivery.tracking_history:
                delivery.tracking_history = []
            
            tracking_entry = {
                "status": status_update["status"],
                "location": status_update.get("location") or delivery.current_location,
                "timestamp": now.isoformat(),
                "description": status_update.get("description") or f"Package {status_update['status']}"
            }
            
            delivery.tracking_history.append(tracking_entry)
            
            db.commit()
            
            print(f"✅ Delivery status updated: {status_update['status']}")
            
            return {
                "success": True,
                "message": "Delivery status updated successfully",
                "waybill_number": waybill_number,
                "status": status_update["status"]
            }
        
        # ❌ Invalid action
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in handle_delivery_request: {str(e)}")
        traceback.print_exc()
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# 🚀 SAB ENDPOINTS - EK HI FUNCTION USE KARENGE
# ============================================

@router.get("/check-pincode/{pincode}")
async def check_pincode_serviceability(pincode: str):
    """Check if Shiprocket delivery is available for pincode"""
    return handle_delivery_request(action="check_pincode", pincode=pincode)


@router.post("/calculate-shipping")
async def calculate_shipping_charges(data: ShippingCalculation):
    """Calculate Shiprocket shipping charges based on pincode and weight"""
    return handle_delivery_request(
        action="calculate_shipping",
        pincode=data.pincode,
        weight=data.weight,
        cod_amount=data.cod_amount
    )


@router.get("/estimate/{pincode}")
async def get_estimated_delivery(pincode: str):
    """Get estimated delivery date for pincode via Shiprocket"""
    return handle_delivery_request(action="estimate_delivery", pincode=pincode)


@router.get("/track/{order_id}")
async def track_delivery(order_id: str, db: Session = Depends(get_db)):
    """Track delivery by order ID"""
    return handle_delivery_request(
        action="track_order",
        order_id=order_id,
        db=db
    )


@router.get("/track-waybill/{waybill_number}")
async def track_by_waybill(waybill_number: str, db: Session = Depends(get_db)):
    """Track delivery by waybill number"""
    return handle_delivery_request(
        action="track_waybill",
        waybill_number=waybill_number,
        db=db
    )


@router.post("/update-status/{waybill_number}")
async def update_delivery_status(
    waybill_number: str,
    status_update: DeliveryStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update delivery status (Admin/Webhook use)"""
    return handle_delivery_request(
        action="update_status",
        waybill_number=waybill_number,
        status_update={
            "status": status_update.status,
            "location": status_update.location,
            "description": status_update.description
        },
        db=db
    )