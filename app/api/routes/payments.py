# backend/app/api/routes/payments.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import hashlib
import hmac
from datetime import datetime
from app.config import settings
from app.services.payment_service import payment_service
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

# ========================================
# Request Models
# ========================================

class RazorpayOrderCreate(BaseModel):
    amount: float
    order_id: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

class RazorpayPaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    order_id: str  # ✅ Added for database update

class PhonePePaymentCreate(BaseModel):
    amount: float
    order_id: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None

class CODOrderCreate(BaseModel):
    order_id: str

class RefundRequest(BaseModel):
    payment_id: str
    amount: Optional[float] = None
    reason: str = "Customer request"

# ========================================
# Razorpay - Create Order
# ========================================

@router.post("/razorpay/create")
async def create_razorpay_order(data: RazorpayOrderCreate):
    """Create Razorpay order for payment"""
    try:
        print(f"📝 Creating Razorpay order")
        print(f"   Order ID: {data.order_id}")
        print(f"   Amount: ₹{data.amount}")
        
        # Use actual payment service (with settings integration)
        result = payment_service.create_order(
            amount=data.amount,
            order_id=data.order_id,
            customer_email=data.customer_email,
            customer_phone=data.customer_phone
        )
        
        if result.get("success"):
            print(f"✅ Order created: {result.get('razorpay_order_id')}")
            
            return {
                "success": True,
                "order": {
                    "id": result.get("razorpay_order_id"),
                    "entity": "order",
                    "amount": result.get("amount"),
                    "currency": result.get("currency"),
                    "receipt": data.order_id,
                    "status": "created"
                },
                "key_id": result.get("key_id"),
                "order_id": data.order_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to create Razorpay order"
            )
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Razorpay - Verify Payment
# ========================================

@router.post("/razorpay/verify")
async def verify_razorpay_payment(
    data: RazorpayPaymentVerify,
    db: Session = Depends(get_db)
):
    """Verify Razorpay payment signature"""
    try:
        print(f"🔍 Verifying payment")
        print(f"   Order ID: {data.order_id}")
        print(f"   Payment ID: {data.razorpay_payment_id}")
        
        # Verify signature using payment service
        result = payment_service.verify_payment(
            razorpay_order_id=data.razorpay_order_id,
            razorpay_payment_id=data.razorpay_payment_id,
            razorpay_signature=data.razorpay_signature
        )
        
        if result.get("verified"):
            print("✅ Payment verified successfully")
            
            # Update order in database
            try:
                from app.models.order import Order
                
                order = db.query(Order).filter(
                    Order.order_id == data.order_id
                ).first()
                
                if order:
                    order.payment_status = "paid"
                    order.payment_method = "online"
                    order.razorpay_payment_id = data.razorpay_payment_id
                    order.razorpay_order_id = data.razorpay_order_id
                    order.updated_at = datetime.utcnow()
                    db.commit()
                    db.refresh(order)
                    print(f"✅ Order {data.order_id} marked as PAID")
                else:
                    print(f"⚠️ Order not found in database")
                    
            except Exception as db_error:
                print(f"⚠️ DB error: {str(db_error)}")
                db.rollback()
            
            return {
                "success": True,
                "verified": True,
                "message": "Payment verified successfully",
                "payment_id": data.razorpay_payment_id,
                "order_id": data.order_id
            }
        else:
            print("❌ Verification failed")
            return {
                "success": False,
                "verified": False,
                "message": "Payment verification failed"
            }
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# PhonePe Payment
# ========================================

@router.post("/phonepe/create")
async def create_phonepe_payment(data: PhonePePaymentCreate):
    """Create PhonePe payment (Coming soon)"""
    try:
        print(f"📱 PhonePe payment request: {data.order_id}")
        
        merchant_transaction_id = f"MT{data.order_id}_{int(datetime.now().timestamp())}"
        
        return {
            "success": True,
            "payment_url": f"https://phonepe.com/pay/{merchant_transaction_id}",
            "merchant_transaction_id": merchant_transaction_id,
            "amount": data.amount,
            "message": "PhonePe integration coming soon",
            "mock": True
        }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Payment Status
# ========================================

@router.get("/status/{payment_id}")
async def check_payment_status(payment_id: str):
    """Check payment status"""
    try:
        print(f"🔍 Checking status: {payment_id}")
        
        result = payment_service.fetch_payment(payment_id)
        
        if result.get("success"):
            payment = result.get("payment", {})
            
            return {
                "success": True,
                "payment_id": payment_id,
                "status": payment.get("status", "unknown"),
                "amount": payment.get("amount", 0) / 100,
                "currency": payment.get("currency", "INR"),
                "method": payment.get("method", ""),
                "created_at": payment.get("created_at", datetime.now().isoformat())
            }
        else:
            return {
                "success": True,
                "payment_id": payment_id,
                "status": "captured",
                "amount": 0,
                "currency": "INR",
                "mock": True
            }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Cash on Delivery
# ========================================

@router.post("/cod")
async def process_cod_order(
    data: CODOrderCreate,
    db: Session = Depends(get_db)
):
    """Process COD order"""
    try:
        print(f"💰 Processing COD: {data.order_id}")
        
        try:
            from app.models.order import Order
            
            order = db.query(Order).filter(
                Order.order_id == data.order_id
            ).first()
            
            if order:
                order.payment_method = "cod"
                order.payment_status = "pending"
                order.updated_at = datetime.utcnow()
                db.commit()
                print(f"✅ Order set to COD")
                
        except Exception as db_error:
            print(f"⚠️ DB error: {str(db_error)}")
            db.rollback()
        
        return {
            "success": True,
            "message": "COD order placed successfully",
            "order_id": data.order_id,
            "payment_method": "cod",
            "payment_status": "pending"
        }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Refund
# ========================================

@router.post("/refund")
async def initiate_refund(data: RefundRequest):
    """Initiate refund"""
    try:
        print(f"💸 Initiating refund: {data.payment_id}")
        
        result = payment_service.create_refund(
            payment_id=data.payment_id,
            amount=data.amount,
            reason=data.reason
        )
        
        if result.get("success"):
            print(f"✅ Refund initiated: {result.get('refund_id')}")
            
            return {
                "success": True,
                "refund_id": result.get("refund_id"),
                "payment_id": data.payment_id,
                "amount": result.get("amount", 0),
                "reason": data.reason,
                "status": result.get("status", "processing"),
                "estimated_days": "5-7 business days"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Refund failed")
            )
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# Health & Config
# ========================================

@router.get("/health")
async def payment_health():
    """Health check"""
    return {
        "status": "healthy",
        "razorpay": {
            "configured": bool(settings.razorpay_key_id),
            "mode": "test" if "test" in settings.razorpay_key_id else "live"
        },
        "services": {
            "razorpay": "active",
            "phonepe": "coming_soon",
            "cod": "active"
        }
    }

@router.get("/config")
async def payment_config():
    """Get payment config (Dev only)"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Development only")
    
    return {
        "razorpay": {
            "configured": bool(settings.razorpay_key_id),
            "key_id": settings.razorpay_key_id,
            "mode": "test" if "test" in settings.razorpay_key_id else "live"
        }
    }