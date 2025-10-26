# backend/app/api/routes/orders.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import traceback

from app.database.connection import get_db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.customer import Customer
from app.models.delivery import Delivery
from app.services.shiprocket_service import shiprocket_service

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

def calculate_shipping_cost(pincode: str, weight: float, subtotal: float, is_cod: bool = False):
    """Calculate shipping cost via Shiprocket"""
    try:
        # Free shipping above 999
        if subtotal >= 999:
            return 0.0
        
        # Calculate via Shiprocket
        cod_amount = subtotal if is_cod else 0
        result = shiprocket_service.calculate_shipping_charges(pincode, weight, cod_amount)
        
        total_charge = result.get("total_charge", 50)
        
        # Cap at reasonable amount
        return min(total_charge, 100)
        
    except Exception as e:
        print(f"⚠️ Shipping calculation error: {str(e)}")
        # Fallback to flat rate
        return 50.0 if subtotal < 999 else 0.0


@router.post("/create")
async def create_order(
    order_request: CreateOrderRequest, 
    db: Session = Depends(get_db)
):
    """Create a new order with Shiprocket delivery"""
    try:
        # Calculate totals
        subtotal = sum(item.price * item.quantity for item in order_request.items)
        
        # Calculate weight (assuming 1kg per item)
        total_weight = sum(item.quantity * 1.0 for item in order_request.items)
        
        # Calculate shipping via Shiprocket
        is_cod = order_request.paymentMethod == "cod"
        shipping_cost = calculate_shipping_cost(
            order_request.shippingAddress.pincode,
            total_weight,
            subtotal,
            is_cod
        )
        
        total = subtotal + shipping_cost
        
        # Generate order ID
        order_id_str = generate_order_id()
        
        # Get or create customer
        customer = None
        
        if order_request.userPhone:
            customer = db.query(Customer).filter(
                Customer.phone == order_request.userPhone
            ).first()
        
        if not customer:
            customer = Customer(
                phone=order_request.userPhone,
                email=order_request.shippingAddress.email,
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
            payment_status=PaymentStatus.COD if is_cod else PaymentStatus.PENDING,
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
        
        # Create Shiprocket shipment
        print(f"📦 Creating Shiprocket shipment for order {order_id_str}")
        
        try:
            # Prepare order data for Shiprocket
            order_data = {
                "order_id": order_id_str,
                "shipping_name": new_order.shipping_name,
                "shipping_phone": new_order.shipping_phone,
                "shipping_email": new_order.shipping_email,
                "shipping_address": new_order.shipping_address,
                "shipping_city": new_order.shipping_city,
                "shipping_state": new_order.shipping_state,
                "shipping_pincode": new_order.shipping_pincode,
                "payment_method": new_order.payment_method,
                "total": float(new_order.total),
                "subtotal": float(new_order.subtotal),
                "shipping_cost": float(new_order.shipping_cost),
                "weight": total_weight,
                "items": [{
                    "product_id": item.productId,
                    "product_name": item.productName,
                    "quantity": item.quantity,
                    "price": item.price
                } for item in order_request.items]
            }
            
            # Create shipment via Shiprocket
            shipment_result = shiprocket_service.create_shipment(order_data)
            
            if shipment_result.get("success"):
                # Create delivery record
                delivery = Delivery(
                    order_id=new_order.id,
                    waybill_number=shipment_result.get("waybill") or shipment_result.get("awb_code", ""),
                    shipment_id=shipment_result.get("shipment_id", ""),
                    current_status="Order Placed",
                    current_location=f"{new_order.shipping_city}, {new_order.shipping_state}",
                    courier_name=shipment_result.get("courier_name", "Shiprocket"),
                    tracking_url=shipment_result.get("tracking_url", ""),
                    estimated_delivery_date=datetime.utcnow() + timedelta(days=5),
                    weight=total_weight,
                    shipping_charge=float(new_order.shipping_cost),
                    tracking_history=[{
                        "status": "Order Placed",
                        "location": f"{new_order.shipping_city}, {new_order.shipping_state}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "description": "Your order has been placed and will be shipped via Shiprocket soon."
                    }]
                )
                
                db.add(delivery)
                
                # Update order with waybill
                new_order.waybill_number = delivery.waybill_number
                new_order.order_status = OrderStatus.PROCESSING
                
                db.commit()
                
                print(f"✅ Shiprocket shipment created: {delivery.waybill_number}")
            else:
                print(f"⚠️ Shiprocket shipment creation failed, order still created")
        
        except Exception as shipment_error:
            print(f"❌ Shipment creation error: {str(shipment_error)}")
            traceback.print_exc()
            # Order still created, delivery can be created later
        
        return {
            "success": True,
            "orderId": new_order.order_id,
            "subtotal": subtotal,
            "shippingCost": shipping_cost,
            "total": total,
            "paymentStatus": new_order.payment_status.value,
            "orderStatus": new_order.order_status.value,
            "estimatedDelivery": new_order.estimated_delivery,
            "waybillNumber": new_order.waybill_number,
            "createdAt": new_order.created_at.isoformat() if new_order.created_at else datetime.now().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Order creation error: {str(e)}")
        traceback.print_exc()
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
        "deliveryStatus": delivery.current_status if delivery else None,
        "courierName": delivery.courier_name if delivery else None
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

@router.get("/{order_id}/invoice")
async def get_order_invoice(order_id: str, db: Session = Depends(get_db)):
    """
    Get Shiprocket invoice PDF for an order
    Returns redirect to Shiprocket invoice or error
    """
    try:
        print(f"\n{'='*70}")
        print(f"📄 GENERATING INVOICE FOR ORDER: {order_id}")
        print(f"{'='*70}\n")
        
        # Get order from database
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if debug mode
        if settings.debug:
            print("⚠️  Debug mode is ON - cannot generate real invoice")
            return JSONResponse({
                "success": False,
                "message": "Invoice generation disabled in debug mode",
                "note": "Set DEBUG=false in .env to enable real Shiprocket invoices",
                "order_id": order_id
            }, status_code=400)
        
        # Get delivery record to find Shiprocket shipment ID
        delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
        
        if not delivery or not delivery.shipment_id:
            return JSONResponse({
                "success": False,
                "message": "Invoice not available yet",
                "note": "Shiprocket shipment not created for this order. Wait 2-3 minutes after order placement.",
                "order_id": order_id
            }, status_code=404)
        
        # Get Shiprocket auth token
        headers = shiprocket_service._get_headers()
        
        if not headers.get("Authorization"):
            raise HTTPException(
                status_code=401, 
                detail="Shiprocket authentication failed"
            )
        
        # Call Shiprocket Invoice API
        url = f"{shiprocket_service.BASE_URL}/orders/print/invoice"
        
        # Try with shipment_id first (more reliable)
        payload = {
            "ids": [delivery.shipment_id]
        }
        
        print(f"📡 Calling Shiprocket Invoice API...")
        print(f"   Shipment ID: {delivery.shipment_id}")
        print(f"   Waybill: {delivery.waybill_number}\n")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 API Response received\n")
            
            # Shiprocket returns invoice URL
            invoice_url = (
                data.get("invoice_url") or 
                data.get("url") or 
                data.get("data", {}).get("invoice_url") or
                data.get("data", {}).get("url")
            )
            
            if invoice_url:
                print(f"✅ Invoice URL: {invoice_url}\n")
                # Redirect to actual Shiprocket invoice PDF
                return RedirectResponse(url=invoice_url)
            
            # Check if base64 PDF is returned
            pdf_data = data.get("pdf") or data.get("data", {}).get("pdf")
            if pdf_data:
                print("📄 Base64 PDF received\n")
                return JSONResponse({
                    "success": True,
                    "pdf_base64": pdf_data,
                    "message": "Decode base64 to display PDF"
                })
            
            # No invoice found
            print(f"⚠️  No invoice URL/PDF in response")
            print(f"   Full response: {data}\n")
            
            return JSONResponse({
                "success": False,
                "message": "Invoice not ready yet",
                "note": "Please wait 2-3 minutes after order creation and try again",
                "shipment_id": delivery.shipment_id,
                "waybill": delivery.waybill_number
            }, status_code=404)
            
        else:
            error_text = response.text
            print(f"❌ Shiprocket API Error: {error_text}\n")
            
            return JSONResponse({
                "success": False,
                "message": "Failed to generate invoice from Shiprocket",
                "error": error_text,
                "status_code": response.status_code,
                "note": "Check if order exists in Shiprocket dashboard"
            }, status_code=response.status_code)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ Invoice Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Optional: Test endpoint to create a real Shiprocket test order
@router.post("/test/shiprocket")
async def create_test_shiprocket_order(db: Session = Depends(get_db)):
    """
    Create a test order in Shiprocket to get real invoice
    Only works when DEBUG=false
    """
    try:
        if settings.debug:
            return {
                "success": False,
                "message": "Test order creation disabled in debug mode",
                "note": "Set DEBUG=false in .env"
            }
        
        # Create test order data
        test_order_id = generate_order_id()
        
        test_order_data = {
            "order_id": test_order_id,
            "shipping_name": "Mohit Sahu (TEST)",
            "shipping_phone": "8887948909",
            "shipping_email": "sahumohit643@gmail.com",
            "shipping_address": "Radha Nagar, Fatehpur",
            "shipping_city": "Fatehpur",
            "shipping_state": "Uttar Pradesh",
            "shipping_pincode": "212601",
            "payment_method": "cod",
            "total": 590.0,
            "subtotal": 540.0,
            "shipping_cost": 50.0,
            "weight": 1.0,
            "items": [{
                "product_id": 1,
                "product_name": "Cold-Pressed Mustard Oil (1L) - TEST",
                "quantity": 1,
                "price": 540.0
            }]
        }
        
        print(f"\n🧪 Creating TEST order in Shiprocket...")
        print(f"   Order ID: {test_order_id}")
        
        # Create shipment
        shipment_result = shiprocket_service.create_shipment(test_order_data)
        
        if shipment_result.get("success"):
            # Save to database
            customer = db.query(Customer).filter(
                Customer.phone == "918887948909"
            ).first()
            
            if not customer:
                customer = Customer(
                    phone="918887948909",
                    email="sahumohit643@gmail.com",
                    full_name="Mohit Sahu (TEST)"
                )
                db.add(customer)
                db.commit()
                db.refresh(customer)
            
            # Create order in DB
            new_order = Order(
                order_id=test_order_id,
                customer_id=customer.id,
                shipping_name="Mohit Sahu (TEST)",
                shipping_phone="8887948909",
                shipping_email="sahumohit643@gmail.com",
                shipping_address="Radha Nagar, Fatehpur",
                shipping_city="Fatehpur",
                shipping_state="Uttar Pradesh",
                shipping_pincode="212601",
                subtotal=540.0,
                shipping_cost=50.0,
                total=590.0,
                payment_method="cod",
                payment_status=PaymentStatus.COD,
                order_status=OrderStatus.PROCESSING,
                waybill_number=shipment_result.get("waybill", ""),
                estimated_delivery="5-7 business days"
            )
            
            db.add(new_order)
            db.commit()
            db.refresh(new_order)
            
            # Create delivery record
            delivery = Delivery(
                order_id=new_order.id,
                waybill_number=shipment_result.get("waybill", ""),
                shipment_id=shipment_result.get("shipment_id", ""),
                current_status="Order Placed",
                current_location="Fatehpur, Uttar Pradesh",
                courier_name=shipment_result.get("courier_name", "Shiprocket"),
                tracking_url=shipment_result.get("tracking_url", ""),
                estimated_delivery_date=datetime.utcnow() + timedelta(days=5),
                weight=1.0,
                shipping_charge=50.0,
                tracking_history=[{
                    "status": "Order Placed",
                    "location": "Fatehpur, Uttar Pradesh",
                    "timestamp": datetime.utcnow().isoformat(),
                    "description": "TEST order placed in Shiprocket"
                }]
            )
            
            db.add(delivery)
            db.commit()
            
            print(f"\n✅ TEST order created successfully!")
            
            return {
                "success": True,
                "message": "Test order created in Shiprocket!",
                "order_id": test_order_id,
                "shipment_id": shipment_result.get("shipment_id"),
                "waybill": shipment_result.get("waybill"),
                "tracking_url": shipment_result.get("tracking_url"),
                "invoice_url": f"/api/orders/{test_order_id}/invoice",
                "next_steps": {
                    "1": f"GET /api/orders/{test_order_id}/invoice to download invoice",
                    "2": f"GET /api/orders/{test_order_id}/track to track shipment",
                    "3": "Login to Shiprocket dashboard to see the order"
                }
            }
        else:
            return {
                "success": False,
                "message": "Failed to create test order in Shiprocket",
                "error": shipment_result
            }
            
    except Exception as e:
        print(f"❌ Test order error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/track")
async def track_order(order_id: str, db: Session = Depends(get_db)):
    """Track order with Shiprocket delivery status"""
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
        "courierName": delivery.courier_name if delivery else None,
        "trackingUpdates": []
    }
    
    # Get live tracking from Shiprocket if shipment_id exists
    if delivery and delivery.shipment_id:
        try:
            live_tracking = shiprocket_service.track_shipment(delivery.shipment_id)
            if live_tracking.get("success"):
                tracking_info["liveTracking"] = live_tracking
                # Update current status from live tracking
                if live_tracking.get("current_status"):
                    tracking_info["deliveryStatus"] = live_tracking["current_status"]
        except Exception as tracking_error:
            print(f"⚠️ Live tracking failed: {str(tracking_error)}")
    
    # Add status history
    if delivery and delivery.tracking_history:
        tracking_info["trackingUpdates"] = delivery.tracking_history
    
    return tracking_info


@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, reason: dict, db: Session = Depends(get_db)):
    """Cancel an order and its Shiprocket delivery"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.order_status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel order with status: {order.order_status.value}"
        )
    
    # Cancel Shiprocket delivery if exists
    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    if delivery and delivery.shipment_id:
        try:
            # TODO: Implement Shiprocket cancellation API
            delivery.current_status = "Cancelled"
            print(f"✅ Delivery cancelled: {delivery.shipment_id}")
        except Exception as e:
            print(f"⚠️ Failed to cancel Shiprocket shipment: {str(e)}")
    
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
    """Calculate order total including Shiprocket shipping"""
    items = data.get("items", [])
    shipping_address = data.get("shipping_address", {})
    payment_method = data.get("payment_method", "cod")
    
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    
    # Calculate weight
    total_weight = sum(item["quantity"] * 1.0 for item in items)
    
    # Calculate shipping via Shiprocket
    is_cod = payment_method == "cod"
    shipping_cost = calculate_shipping_cost(
        shipping_address.get("pincode", ""), 
        total_weight,
        subtotal,
        is_cod
    )
    
    return {
        "subtotal": subtotal,
        "shippingCost": shipping_cost,
        "total": subtotal + shipping_cost,
        "freeShippingEligible": subtotal >= 999
    }