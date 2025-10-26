# backend/app/routers/admin_orders.py (CREATE THIS NEW FILE)
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.customer import Customer

router = APIRouter()

# ==================== REQUEST MODELS ====================
class UpdateStatusRequest(BaseModel):
    status: str

# ==================== HELPER: VERIFY ADMIN ====================
def verify_admin_access(email: str = None, phone: str = None, db: Session = None):
    """Verify if user is admin"""
    if not email and not phone:
        raise HTTPException(status_code=401, detail="Email or phone required for authentication")
    
    customer = None
    if email:
        customer = db.query(Customer).filter(Customer.email == email).first()
    elif phone:
        # Format phone if needed
        phone = ''.join(filter(str.isdigit, phone))
        if not phone.startswith('91') and len(phone) == 10:
            phone = f"91{phone}"
        customer = db.query(Customer).filter(Customer.phone == phone).first()
    
    if not customer:
        print(f"❌ User not found: {email or phone}")
        raise HTTPException(status_code=404, detail="User not found")
    
    if not customer.is_admin:
        print(f"🚫 Non-admin access attempt by: {customer.email or customer.phone}")
        raise HTTPException(status_code=403, detail="Admin access required")
    
    print(f"✅ Admin verified: {customer.email or customer.phone}")
    return customer

# ==================== GET ALL ORDERS ====================
@router.get("/orders")
async def get_all_orders(
    status: Optional[str] = Query(None),
    email: str = Query(None),
    phone: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get all orders for admin dashboard"""
    try:
        # Verify admin
        verify_admin_access(email=email, phone=phone, db=db)
        
        # Build query
        query = db.query(Order)
        
        # Filter by status if provided
        if status and status != "all":
            query = query.filter(Order.order_status == status)
        
        # Get orders sorted by newest first
        orders = query.order_by(Order.created_at.desc()).all()
        
        # Format response
        orders_data = []
        for order in orders:
            orders_data.append({
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "shipping_address": {
                    "fullName": order.shipping_name,
                    "phone": order.shipping_phone,
                    "email": order.shipping_email,
                    "address": order.shipping_address,
                    "city": order.shipping_city,
                    "state": order.shipping_state,
                    "pincode": order.shipping_pincode,
                    "landmark": order.shipping_landmark
                },
                "subtotal": float(order.subtotal) if order.subtotal else 0,
                "shipping_cost": float(order.shipping_cost) if order.shipping_cost else 0,
                "discount": float(order.discount) if order.discount else 0,
                "tax": float(order.tax) if order.tax else 0,
                "total": float(order.total) if order.total else 0,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status.value if order.payment_status else "pending",
                "order_status": order.order_status.value if order.order_status else "pending",
                "shipment_id": order.waybill_number,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
                "items": [
                    {
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                        "price": float(item.price),
                        "total": float(item.total),
                        "size": item.size,
                        "unit": item.unit,
                        "image": item.product_image
                    }
                    for item in order.items
                ]
            })
        
        print(f"✅ Fetched {len(orders_data)} orders for admin")
        
        return {
            "success": True,
            "orders": orders_data,
            "total": len(orders_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_all_orders: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== UPDATE ORDER STATUS ====================
@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    request: UpdateStatusRequest,
    email: str = Query(None),
    phone: str = Query(None),
    db: Session = Depends(get_db)
):
    """Update order status - Admin only"""
    try:
        # Verify admin
        verify_admin_access(email=email, phone=phone, db=db)
        
        # Find order
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Validate status
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"]
        if request.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Update status
        old_status = order.order_status.value if order.order_status else "unknown"
        order.order_status = OrderStatus(request.status)
        
        # Update delivered_at if status changed to delivered
        if request.status == "delivered" and not order.delivered_at:
            order.delivered_at = datetime.now()
        
        db.commit()
        db.refresh(order)
        
        print(f"✅ Order {order_id} status updated: {old_status} → {request.status}")
        
        return {
            "success": True,
            "message": "Order status updated successfully",
            "order_id": order.order_id,
            "old_status": old_status,
            "new_status": order.order_status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating order status: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CREATE SHIPMENT ====================
@router.post("/orders/{order_id}/ship")
async def create_shipment(
    order_id: str,
    email: str = Query(None),
    phone: str = Query(None),
    db: Session = Depends(get_db)
):
    """Create shipment for order - Admin only"""
    try:
        # Verify admin
        verify_admin_access(email=email, phone=phone, db=db)
        
        # Find order
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if shipment already exists
        if order.waybill_number:
            return {
                "success": False,
                "message": "Shipment already exists",
                "waybill_number": order.waybill_number
            }
        
        # Generate waybill number
        import random
        import string
        waybill = 'WB' + ''.join(random.choices(string.digits, k=12))
        
        # Update order
        order.waybill_number = waybill
        order.order_status = OrderStatus.SHIPPED
        order.estimated_delivery = "3-5 business days"
        
        db.commit()
        db.refresh(order)
        
        print(f"✅ Shipment created for order {order_id}: {waybill}")
        
        return {
            "success": True,
            "message": "Shipment created successfully",
            "waybill_number": waybill,
            "estimated_delivery": "3-5 business days",
            "order_status": order.order_status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating shipment: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PRINT INVOICE (PLACEHOLDER) ====================
@router.get("/orders/{order_id}/invoice")
async def get_invoice(
    order_id: str,
    email: str = Query(None),
    phone: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get invoice data - Admin only (PDF generation can be added later)"""
    try:
        # Verify admin
        verify_admin_access(email=email, phone=phone, db=db)
        
        # Find order
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Return invoice data (you can generate PDF later)
        invoice_data = {
            "order_id": order.order_id,
            "customer_name": order.shipping_name,
            "customer_email": order.shipping_email,
            "customer_phone": order.shipping_phone,
            "address": {
                "line1": order.shipping_address,
                "city": order.shipping_city,
                "state": order.shipping_state,
                "pincode": order.shipping_pincode
            },
            "items": [
                {
                    "name": item.product_name,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "total": float(item.total)
                }
                for item in order.items
            ],
            "subtotal": float(order.subtotal),
            "shipping": float(order.shipping_cost),
            "discount": float(order.discount),
            "tax": float(order.tax),
            "total": float(order.total),
            "payment_method": order.payment_method,
            "payment_status": order.payment_status.value,
            "order_date": order.created_at.isoformat() if order.created_at else None
        }
        
        print(f"✅ Invoice generated for order {order_id}")
        
        return {
            "success": True,
            "invoice": invoice_data,
            "message": "Invoice data retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))