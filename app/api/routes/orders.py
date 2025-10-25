from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json

from app.database.connection import get_db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.customer import Customer
from app.models.delivery import Delivery
from app.services.delhivery_service import delhivery_service

router = APIRouter()

class OrderItemSchema(BaseModel):
    productId: int
    productName: str
    quantity: int
    price: float
    size: str
    unit: str

class ShippingAddress(BaseModel):
    fullName: str
    phone: str
    email: EmailStr
    address: str
    city: str
    state: str
    pincode: str
    landmark: Optional[str] = None

class CreateOrderRequest(BaseModel):
    items: List[OrderItemSchema]
    shippingAddress: ShippingAddress
    paymentMethod: str
    userPhone: Optional[str] = None

def generate_order_id():
    """Generate unique order ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PD{timestamp}"

def calculate_shipping_cost(pincode: str, subtotal: float):
    """Calculate shipping cost based on pincode and subtotal"""
    if subtotal >= 999:
        return 0.0
    return 50.0

# backend/app/api/routes/orders.py
# backend/app/api/routes/orders.py
# Line 73-109 (create_delivery_async function)

async def create_delivery_async(order_id: int, db: Session):
    """Create delivery after order creation"""
    try:
        order_obj = db.query(Order).filter(Order.id == order_id).first()
        
        if not order_obj:
            return
        
        # Generate waybill number
        waybill_number = f"PDEL{order_obj.order_id[2:]}"
        
        print(f"🚚 Creating delivery for order {order_obj.order_id}")
        print(f"✅ Mock shipment created: {waybill_number}")
        
        # Update order with waybill
        order_obj.waybill_number = waybill_number
        
        # ✅ FIX: Only change this part (Line 87-96)
        delivery = Delivery(
            order_id=order_id,
            waybill_number=waybill_number,        # ✅ Changed from 'waybill'
            shipment_id=f"SHIP{order_obj.order_id[2:]}",
            current_status="Order Placed",
            current_location=f"{order_obj.shipping_city}, {order_obj.shipping_state}",
            courier_name="Delhivery",
            tracking_url=f"https://www.delhivery.com/track/package/{waybill_number}",
            estimated_delivery_date=datetime.utcnow() + timedelta(days=5),
            weight=1.0,
            shipping_charge=float(order_obj.shipping_cost),
            tracking_history=[{
                "status": "Order Placed",
                "location": f"{order_obj.shipping_city}, {order_obj.shipping_state}",
                "timestamp": datetime.utcnow().isoformat(),
                "description": "Your order has been placed successfully and will be shipped soon."
            }]
        )
        
        db.add(delivery)
        db.commit()
        
        print(f"✅ Delivery tracking created for order {order_obj.order_id}")
        
    except Exception as e:
        print(f"❌ Error creating delivery: {str(e)}")
        traceback.print_exc()
        db.rollback()

@router.post("/create")
async def create_order(
    order_request: CreateOrderRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new order with automatic delivery creation"""
    try:
        # Calculate totals
        subtotal = sum(item.price * item.quantity for item in order_request.items)
        shipping_cost = calculate_shipping_cost(
            order_request.shippingAddress.pincode, 
            subtotal
        )
        total = subtotal + shipping_cost
        
        # Generate order ID
        order_id_str = generate_order_id()
        
        # Get or create customer (support both phone and email)
        customer = None
        
        if order_request.userPhone:
            customer = db.query(Customer).filter(
                Customer.phone == order_request.userPhone
            ).first()
        elif order_request.userEmail:
            customer = db.query(Customer).filter(
                Customer.email == order_request.userEmail
            ).first()
        
        if not customer:
            customer = Customer(
                phone=order_request.userPhone,
                email=order_request.userEmail or order_request.shippingAddress.email,
                full_name=order_request.shippingAddress.fullName
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
        
        # Create order
        new_order = Order(
            order_id=order_id_str,
            customer_id=customer.id,
            shipping_name=order_request.shippingAddress.fullName,
            shipping_phone=order_request.shippingAddress.phone,
            shipping_email=order_request.shippingAddress.email,
            shipping_address=order_request.shippingAddress.address,
            shipping_city=order_request.shippingAddress.city,
            shipping_state=order_request.shippingAddress.state,
            shipping_pincode=order_request.shippingAddress.pincode,
            shipping_landmark=order_request.shippingAddress.landmark,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
            payment_method=order_request.paymentMethod,
            payment_status=PaymentStatus.COD if order_request.paymentMethod == "cod" else PaymentStatus.PENDING,
            order_status=OrderStatus.CONFIRMED,
            estimated_delivery="3-5 business days"
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        # Create order items
        for item in order_request.items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.productId,
                product_name=item.productName,
                product_slug="",
                product_image="",
                size=item.size,
                unit=item.unit,
                quantity=item.quantity,
                price=item.price,
                total=item.price * item.quantity
            )
            db.add(order_item)
        
        db.commit()
        db.refresh(new_order)
        
        # ✅ Pass only order_id, not the whole object
        # ✅ Get a new db session for background task
        from app.database.connection import SessionLocal
        bg_db = SessionLocal()
        
        try:
            background_tasks.add_task(create_delivery_async, new_order.id, bg_db)
        except Exception as bg_error:
            print(f"⚠️ Background task error: {str(bg_error)}")
        
        return {
            "success": True,
            "orderId": new_order.order_id,
            "subtotal": subtotal,
            "shippingCost": shipping_cost,
            "total": total,
            "paymentStatus": new_order.payment_status.value,
            "orderStatus": new_order.order_status.value,
            "estimatedDelivery": new_order.estimated_delivery,
            "createdAt": new_order.created_at.isoformat() if new_order.created_at else datetime.now().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Order creation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@router.post("/create")
async def create_order(
    order_request: CreateOrderRequest, 
    db: Session = Depends(get_db)
):
    """Create a new order with automatic delivery creation"""
    try:
        # ... existing order creation code ...
        
        db.commit()
        db.refresh(new_order)
        
        # ✅ Create delivery synchronously (simpler, no session issues)
        try:
            items = db.query(OrderItem).filter(OrderItem.order_id == new_order.id).all()
            total_weight = sum(item.quantity * 1.0 for item in items)
            
            order_data = {
                "order_id": new_order.order_id,
                "shipping_name": new_order.shipping_name,
                "shipping_phone": new_order.shipping_phone,
                "shipping_address": new_order.shipping_address,
                "shipping_city": new_order.shipping_city,
                "shipping_state": new_order.shipping_state,
                "shipping_pincode": new_order.shipping_pincode,
                "payment_method": new_order.payment_method,
                "total": float(new_order.total),
                "weight": total_weight,
                "total_quantity": sum(item.quantity for item in items),
                "products_desc": ", ".join([item.product_name for item in items])
            }
            
            result = delhivery_service.create_shipment(order_data)
            
            if result.get("success"):
                delivery = Delivery(
                    order_id=new_order.id,
                    waybill=result["waybill"],
                    shipment_id=result.get("shipment_id", ""),
                    current_status="Pending",
                    tracking_url=result.get("tracking_url", ""),
                    weight=total_weight,
                    status_history=json.dumps([{
                        "status": "Pending",
                        "message": "Shipment created",
                        "timestamp": datetime.now().isoformat()
                    }])
                )
                db.add(delivery)
                new_order.waybill_number = result["waybill"]
                new_order.order_status = OrderStatus.PROCESSING
                db.commit()
                print(f"✅ Delivery created for order {new_order.order_id}")
        
        except Exception as delivery_error:
            print(f"⚠️ Delivery creation failed: {str(delivery_error)}")
            # Order still created, delivery can be created later
        
        return {
            "success": True,
            "orderId": new_order.order_id,
            # ... rest of response
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@router.get("/{order_id}")
async def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get order by ID with delivery info"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get delivery info
    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    
    return {
        "orderId": order.order_id,
        "items": [{
            "productId": item.product_id,
            "productName": item.product_name,
            "quantity": item.quantity,
            "price": item.price,
            "size": item.size,
            "unit": item.unit
        } for item in order.items],
        "shippingAddress": {
            "fullName": order.shipping_name,
            "phone": order.shipping_phone,
            "email": order.shipping_email,
            "address": order.shipping_address,
            "city": order.shipping_city,
            "state": order.shipping_state,
            "pincode": order.shipping_pincode,
            "landmark": order.shipping_landmark
        },
        "subtotal": order.subtotal,
        "shippingCost": order.shipping_cost,
        "total": order.total,
        "paymentMethod": order.payment_method,
        "paymentStatus": order.payment_status.value,
        "orderStatus": order.order_status.value,
        "createdAt": order.created_at.isoformat() if order.created_at else None,
        "estimatedDelivery": order.estimated_delivery,
        "waybillNumber": order.waybill_number,
        "trackingUrl": delivery.tracking_url if delivery else None,
        "deliveryStatus": delivery.current_status if delivery else None
    }


@router.get("/user/phone/{phone}")
async def get_user_orders_by_phone(phone: str, db: Session = Depends(get_db)):
    """Get all orders for a user by phone number"""
    formatted_phone = phone if phone.startswith('91') else f"91{phone}" if len(phone) == 10 else phone
    
    customer = db.query(Customer).filter(Customer.phone == formatted_phone).first()
    if not customer:
        return {"orders": []}
    
    orders = db.query(Order).filter(Order.customer_id == customer.id).order_by(Order.created_at.desc()).all()
    
    return {
        "orders": [{
            "orderId": order.order_id,
            "total": order.total,
            "orderStatus": order.order_status.value,
            "paymentStatus": order.payment_status.value,
            "createdAt": order.created_at.isoformat() if order.created_at else None,
            "itemsCount": len(order.items),
            "waybillNumber": order.waybill_number
        } for order in orders]
    }


@router.get("/{order_id}/track")
async def track_order(order_id: str, db: Session = Depends(get_db)):
    """Track order with delivery status"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    
    tracking_info = {
        "orderId": order.order_id,
        "status": order.order_status.value,
        "paymentStatus": order.payment_status.value,
        "estimatedDelivery": order.estimated_delivery,
        "waybillNumber": order.waybill_number,
        "trackingUrl": delivery.tracking_url if delivery else None,
        "deliveryStatus": delivery.current_status if delivery else None,
        "currentLocation": delivery.current_location if delivery else None,
        "trackingUpdates": []
    }
    
    # Get live tracking if waybill exists
    if delivery and delivery.waybill:
        live_tracking = delhivery_service.track_shipment(delivery.waybill)
        if live_tracking.get("success"):
            tracking_info["liveTracking"] = live_tracking
    
    # Add status history
    if delivery and delivery.status_history:
        tracking_info["trackingUpdates"] = json.loads(delivery.status_history)
    
    return tracking_info


@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, reason: dict, db: Session = Depends(get_db)):
    """Cancel an order and its delivery"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.order_status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel order with status: {order.order_status.value}"
        )
    
    # Cancel delivery if exists
    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    if delivery and delivery.waybill:
        delhivery_service.cancel_shipment(delivery.waybill)
        delivery.current_status = "Cancelled"
    
    # Update order
    order.order_status = OrderStatus.CANCELLED
    order.admin_notes = f"Cancelled: {reason.get('reason', 'User requested cancellation')}"
    
    db.commit()
    
    return {
        "success": True,
        "message": "Order cancelled successfully",
        "orderId": order_id
    }


@router.post("/calculate")
async def calculate_order_total(data: dict):
    """Calculate order total including shipping"""
    items = data.get("items", [])
    shipping_address = data.get("shipping_address", {})
    
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    shipping_cost = calculate_shipping_cost(
        shipping_address.get("pincode", ""), 
        subtotal
    )
    
    return {
        "subtotal": subtotal,
        "shippingCost": shipping_cost,
        "total": subtotal + shipping_cost
    }