# backend/app/api/routes/whatsapp.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.config import settings
from app.services.whatsapp_service import whatsapp_service

router = APIRouter()

# ========================================
# Request Models
# ========================================

class OrderConfirmation(BaseModel):
    order_id: str
    phone_number: str
    customer_name: str
    total_amount: float
    items_count: int

class ShippingUpdate(BaseModel):
    order_id: str
    phone_number: str
    waybill: str
    courier_name: str
    estimated_delivery: str

class DeliveryNotification(BaseModel):
    order_id: str
    phone_number: str
    customer_name: str

class SendOTP(BaseModel):
    phone_number: str

class VerifyOTP(BaseModel):
    phone_number: str
    otp: str

class CustomMessage(BaseModel):
    phone_number: str
    message: str

# ========================================
# Order Confirmation
# ========================================

@router.post("/order-confirmation")
async def send_order_confirmation(data: OrderConfirmation):
    """Send order confirmation via WhatsApp"""
    try:
        print(f"📱 Sending order confirmation to {data.phone_number}")
        
        result = whatsapp_service.send_order_confirmation(
            phone_number=data.phone_number,
            order_id=data.order_id,
            customer_name=data.customer_name,
            total_amount=data.total_amount,
            items_count=data.items_count
        )
        
        if result.get("success"):
            print(f"✅ Order confirmation sent")
            return {
                "success": True,
                "message": "Order confirmation sent successfully",
                "phone_number": data.phone_number,
                "order_id": data.order_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send order confirmation"
            )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Shipping Update
# ========================================

@router.post("/shipping-update")
async def send_shipping_update(data: ShippingUpdate):
    """Send shipping update via WhatsApp"""
    try:
        print(f"📦 Sending shipping update to {data.phone_number}")
        
        result = whatsapp_service.send_shipping_update(
            phone_number=data.phone_number,
            order_id=data.order_id,
            waybill=data.waybill,
            courier_name=data.courier_name,
            estimated_delivery=data.estimated_delivery
        )
        
        if result.get("success"):
            print(f"✅ Shipping update sent")
            return {
                "success": True,
                "message": "Shipping update sent successfully",
                "phone_number": data.phone_number,
                "order_id": data.order_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send shipping update"
            )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Delivery Notification
# ========================================

@router.post("/delivery-notification")
async def send_delivery_notification(data: DeliveryNotification):
    """Send delivery notification via WhatsApp"""
    try:
        print(f"✅ Sending delivery notification to {data.phone_number}")
        
        result = whatsapp_service.send_delivery_notification(
            phone_number=data.phone_number,
            order_id=data.order_id,
            customer_name=data.customer_name
        )
        
        if result.get("success"):
            print(f"✅ Delivery notification sent")
            return {
                "success": True,
                "message": "Delivery notification sent successfully",
                "phone_number": data.phone_number,
                "order_id": data.order_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send delivery notification"
            )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# OTP
# ========================================

@router.post("/send-otp")
async def send_otp(data: SendOTP):
    """Send OTP for verification"""
    try:
        print(f"🔐 Sending OTP to {data.phone_number}")
        
        result = whatsapp_service.send_otp(data.phone_number)
        
        if result.get("success"):
            print(f"✅ OTP sent")
            return {
                "success": True,
                "message": "OTP sent successfully",
                "phone_number": data.phone_number,
                "expires_in": result.get("expires_in", 600)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send OTP"
            )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-otp")
async def verify_otp(data: VerifyOTP):
    """Verify OTP"""
    try:
        print(f"🔍 Verifying OTP for {data.phone_number}")
        
        result = whatsapp_service.verify_otp(
            phone_number=data.phone_number,
            otp=data.otp
        )
        
        if result.get("verified"):
            print(f"✅ OTP verified")
            return {
                "success": True,
                "verified": True,
                "message": "OTP verified successfully",
                "phone_number": data.phone_number
            }
        else:
            return {
                "success": False,
                "verified": False,
                "message": result.get("error", "Invalid OTP")
            }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Custom Message
# ========================================

@router.post("/send-message")
async def send_custom_message(data: CustomMessage):
    """Send custom message via WhatsApp"""
    try:
        print(f"💬 Sending custom message to {data.phone_number}")
        
        result = whatsapp_service.send_custom_message(
            phone_number=data.phone_number,
            message=data.message
        )
        
        if result.get("success"):
            print(f"✅ Message sent")
            return {
                "success": True,
                "message": "Message sent successfully",
                "phone_number": data.phone_number
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send message"
            )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Health Check
# ========================================

@router.get("/health")
async def whatsapp_health():
    """WhatsApp service health check"""
    return {
        "status": "healthy",
        "whatsapp": {
            "configured": bool(settings.whatsapp_api_token),
            "business_phone": settings.whatsapp_business_phone
        }
    }