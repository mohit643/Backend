# backend/app/api/routes/orders.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import traceback
import requests
from fastapi.responses import JSONResponse, RedirectResponse
from app.database.connection import get_db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.customer import Customer
from app.models.delivery import Delivery
from app.services.shiprocket_service import shiprocket_service
from app.config.settings import settings
from app.config.shipping_config import shipping_config

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
    shippingCharge: Optional[float] = 0
    codCharge: Optional[float] = 0
    subtotal: Optional[float] = 0
    total: Optional[float] = None


def calculate_shipping_cost(pincode: str, weight: float, subtotal: float, is_cod: bool = False):
    """Calculate shipping cost via Shiprocket - ✅ Uses REAL rates"""
    try:
        print(f"\n{'='*60}")
        print(f"💰 CALCULATING SHIPPING COST")
        print(f"📍 Pincode: {pincode}")
        print(f"⚖️  Weight: {weight} kg")
        print(f"💵 Subtotal: ₹{subtotal}")
        print(f"💰 COD: {is_cod}")
        print(f"{'='*60}\n")
        
        # ✅ USE CONFIG - Replace hardcoded threshold
        if shipping_config.is_free_shipping_eligible(subtotal):
            print(f"✅ Free shipping (subtotal >= ₹{shipping_config.FREE_SHIPPING_THRESHOLD})")
            return 0.0
        
        # ✅ Get REAL shipping cost from Shiprocket
        print("📡 Calling Shiprocket serviceability API...")
        result = shiprocket_service.check_pincode_serviceability(
            pincode=pincode,
            cod=is_cod
        )
        
        print(f"📦 Shiprocket result: {result}")
        
        if result.get("serviceable"):
            # ✅ Extract REAL rates from Shiprocket
            shipping_charge = result.get("shipping_charge", 50)
            cod_charges = result.get("cod_charges", 0) if is_cod else 0
            
            total_charge = shipping_charge + cod_charges
            
            print(f"✅ Shiprocket rates:")
            print(f"   📦 Base Shipping: ₹{shipping_charge}")
            print(f"   💰 COD Charges: ₹{cod_charges}")
            print(f"   💵 Total Charge: ₹{total_charge}")
            
            # ✅ Return ACTUAL Shiprocket rate (no capping, no hardcoding)
            return round(total_charge, 2)
        else:
            print("⚠️ Pincode not serviceable by Shiprocket")
            # Return fallback only if pincode not serviceable
            return 50.0
        
    except Exception as e:
        print(f"❌ Shipping calculation error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # ✅ USE CONFIG for fallback
        fallback = shipping_config.DEFAULT_SHIPPING_CHARGE if not shipping_config.is_free_shipping_eligible(subtotal) else 0.0
        print(f"⚠️ Using fallback rate: ₹{fallback}")
        return fallback
    
def generate_order_id():
    """Generate unique order ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PD{timestamp}"

def calculate_shipping_cost(pincode: str, weight: float, subtotal: float, is_cod: bool = False):
    """Calculate shipping cost via Shiprocket - ✅ Uses REAL rates"""
    try:
        print(f"\n{'='*60}")
        print(f"💰 CALCULATING SHIPPING COST")
        print(f"📍 Pincode: {pincode}")
        print(f"⚖️  Weight: {weight} kg")
        print(f"💵 Subtotal: ₹{subtotal}")
        print(f"💰 COD: {is_cod}")
        print(f"{'='*60}\n")
        
        # Free shipping above 999
        if subtotal >= 999:
            print("✅ Free shipping (subtotal >= ₹999)")
            return 0.0
        
        # ✅ Get REAL shipping cost from Shiprocket
        print("📡 Calling Shiprocket serviceability API...")
        result = shiprocket_service.check_pincode_serviceability(
            pincode=pincode,
            cod=is_cod
        )
        
        print(f"📦 Shiprocket result: {result}")
        
        if result.get("serviceable"):
            # ✅ Extract REAL rates from Shiprocket
            shipping_charge = result.get("shipping_charge", 50)
            cod_charges = result.get("cod_charges", 0) if is_cod else 0
            
            total_charge = shipping_charge + cod_charges
            
            print(f"✅ Shiprocket rates:")
            print(f"   📦 Base Shipping: ₹{shipping_charge}")
            print(f"   💰 COD Charges: ₹{cod_charges}")
            print(f"   💵 Total Charge: ₹{total_charge}")
            
            # ✅ Return ACTUAL Shiprocket rate (no capping, no hardcoding)
            return round(total_charge, 2)
        else:
            print("⚠️ Pincode not serviceable by Shiprocket")
            # Return fallback only if pincode not serviceable
            return 50.0
        
    except Exception as e:
        print(f"❌ Shipping calculation error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback to flat rate only on error
        fallback = 50.0 if subtotal < 999 else 0.0
        print(f"⚠️ Using fallback rate: ₹{fallback}")
        return fallback


@router.post("/create")
async def create_order(
    order_request: CreateOrderRequest, 
    db: Session = Depends(get_db)
):
    """Create a new order with Shiprocket delivery"""
    try:
        # ✅ Use frontend's calculations if provided
        if order_request.total is not None:
            print(f"✅ Using frontend's calculated charges:")
            print(f"   Subtotal: ₹{order_request.subtotal}")
            print(f"   Shipping: ₹{order_request.shippingCharge}")
            print(f"   COD: ₹{order_request.codCharge}")
            print(f"   Total: ₹{order_request.total}")
            
            subtotal = order_request.subtotal
            shipping_cost = order_request.shippingCharge
            total = order_request.total
            
        else:
            # Fallback: Calculate ourselves
            print("⚠️ Frontend didn't send charges, calculating...")
            
            subtotal = sum(item.price * item.quantity for item in order_request.items)
            total_weight = sum(item.quantity * 1.0 for item in order_request.items)
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

      
    #    db.commit()
    #     db.refresh(new_order)
        
        # --- 3. Shiprocket Shipment Creation (Using Real Warehouse Details) ---
        
        # Prepare Order Items for Shiprocket
        order_items_for_shiprocket = [{
            "name": item.product_name,
            "sku": f"PD-{item.product_id}-{item.size}", 
            "units": item.quantity,
            "selling_price": item.price,
            "hsn": "4819" # Placeholder HSN/SAC
        } for item in new_order.items]

        print("🔄 Preparing payload with WAREHOUSE details for Shiprocket...")

        # Construct the payload using WAREHOUSE settings for the pickup details.
        order_data_for_shiprocket = {
            "order_id": order_id_str,
            "order_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            
            # --- START: SHIPPER (PICKUP) DETAILS from settings ---
            # Shiprocket expects an existing 'pickup_location' name. I will use the warehouse name.
            "pickup_location": settings.warehouse_name, 
            
            # Use the shipping address from the order request for the customer (destination)
            "billing_customer_name": new_order.shipping_name,
            "billing_email": new_order.shipping_email,
            "billing_phone": new_order.shipping_phone,
            "billing_address": new_order.shipping_address,
            "billing_city": new_order.shipping_city,
            "billing_pincode": new_order.shipping_pincode,
            "billing_state": new_order.shipping_state,
            "billing_country": "India", 
            
            "shipping_customer_name": new_order.shipping_name,
            "shipping_email": new_order.shipping_email,
            "shipping_phone": new_order.shipping_phone,
            "shipping_address": new_order.shipping_address,
            "shipping_city": new_order.shipping_city,
            "shipping_pincode": new_order.shipping_pincode,
            "shipping_state": new_order.shipping_state,
            "shipping_country": "India",
            
            "payment_method": order_request.paymentMethod,
            "sub_total": subtotal,
            "shipping_charges": shipping_cost,
            "total_amount": total,
            "order_items": order_items_for_shiprocket,
            "weight": round(total_weight, 3), # Must be in kg
        }

        print("📡 Creating shipment via REAL Shiprocket service...")
        
        # Call the actual Shiprocket service because DEBUG=false in .env
        shipment_result = shiprocket_service.create_shipment(order_data_for_shiprocket)
        
        print(f"📦 Shiprocket response: {shipment_result}")

        # --- 4. Handle Shiprocket Response and Update Database ---
        
        if shipment_result.get("success"):
            # Update the Order object with Shiprocket IDs
            new_order.order_status = OrderStatus.PROCESSING 
            new_order.shiprocket_order_id = shipment_result.get("shiprocket_order_id")
            new_order.shipment_id = shipment_result.get("shipment_id")
            new_order.awb_code = shipment_result.get("awb_code") or shipment_result.get("waybill")
            new_order.courier_id = shipment_result.get("courier_id")
            new_order.waybill_number = new_order.awb_code
            new_order.courier_name = shipment_result.get("courier_name", "Shiprocket")
            
            # Create a separate Delivery record
            delivery = Delivery(
                order_id=new_order.id,
                waybill_number=new_order.waybill_number,
                shipment_id=new_order.shipment_id,
                current_status="Pickup Scheduled",
                current_location=settings.warehouse_city,
                courier_name=new_order.courier_name,
                tracking_url=shipment_result.get("tracking_url", ""),
                estimated_delivery_date=datetime.utcnow() + timedelta(days=5),
                weight=total_weight,
                shipping_charge=shipping_cost
            )
            db.add(delivery)

            db.commit()
            db.refresh(new_order)
            
            print(f"✅ REAL Shipment created and DB updated. AWB: {new_order.awb_code}")
            
        else:
            # Shiprocket failed in LIVE mode. Log error and raise exception for the user.
            new_order.admin_notes = f"Shiprocket Failed (Live): {json.dumps(shipment_result)}"
            db.commit()
            
            error_detail = shipment_result.get("message", "Shiprocket failed to create shipment.")
            
            print(f"❌ Shiprocket creation failed for Order {order_id_str}. Error: {error_detail}")
            # Raise exception to inform the user that the order was placed but shipment failed (critical).
            raise HTTPException(status_code=500, detail=f"Order placed but shipment booking failed. Please retry later or contact support. Error: {error_detail}")

        # --- 5. Final Response ---
        print(f"✅ Order created successfully")
        
        return {
            "success": True,
            "message": "Order created successfully",
            "orderId": order_id_str,
            "total": float(total),
            "subtotal": float(subtotal),
            "shipping": float(shipping_cost),
            "awb_code": new_order.awb_code, # Return AWB for immediate display
            "shipmentCreated": True
        }
        
    except Exception as e:
        # ... (Exception handling remains the same) ...
        print(f"❌ Error creating order: {str(e)}")
        db.rollback()
        traceback.print_exc()
        # Ensure that if it's an HTTPException, we re-raise it, otherwise, use a generic error.
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error during order creation.")


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
        
        # ✅ SHIPROCKET FIELDS
        "shiprocketOrderId": order.shiprocket_order_id,
        "shipmentId": order.shipment_id,
        "awbCode": order.awb_code,
        "courierId": order.courier_id,
        
        # DELIVERY FIELDS
        "waybillNumber": order.waybill_number,
        "trackingUrl": delivery.tracking_url if delivery else None,
        "deliveryStatus": delivery.current_status if delivery else None,
        "courierName": order.courier_name or (delivery.courier_name if delivery else None)
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
    """Get Shiprocket invoice PDF"""
    try:
        print(f"\n{'='*70}")
        print(f"📄 GENERATING INVOICE FOR ORDER: {order_id}")
        print(f"{'='*70}\n")
        
        # Get order
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check debug mode
        if settings.debug:
            return JSONResponse({
                "success": False,
                "message": "Invoice disabled in debug mode",
                "note": "Set DEBUG=false in .env"
            }, status_code=400)
        
        # Get delivery
        delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
        
        if not delivery:
            return JSONResponse({
                "success": False,
                "message": "Shipment not created yet",
                "note": "Wait 2-3 minutes after order placement"
            }, status_code=404)
        
        # Get Shiprocket headers
        headers = shiprocket_service._get_headers()
        
        # ✅ FIX: Use waybill to find Shiprocket order ID
        # First get order details from Shiprocket
        search_url = f"{shiprocket_service.BASE_URL}/orders"
        params = {"awb_code": delivery.waybill_number}
        
        print(f"🔍 Searching for order with AWB: {delivery.waybill_number}")
        
        search_response = requests.get(
            search_url,
            headers=headers,
            params=params,
            timeout=30
        )
        
        if search_response.status_code != 200:
            return JSONResponse({
                "success": False,
                "message": "Order not found in Shiprocket",
                "note": "Please wait 5-10 minutes after order placement"
            }, status_code=404)
        
        search_data = search_response.json()
        orders_list = search_data.get("data", [])
        
        if not orders_list:
            return JSONResponse({
                "success": False,
                "message": "Invoice not ready yet",
                "note": "Shiprocket order not synced. Wait 5-10 minutes."
            }, status_code=404)
        
        # Get Shiprocket order ID
        shiprocket_order_id = orders_list[0].get("id")
        
        print(f"✅ Found Shiprocket Order ID: {shiprocket_order_id}")
        
        # Now generate invoice
        invoice_url = f"{shiprocket_service.BASE_URL}/orders/print/invoice"
        payload = {"ids": [shiprocket_order_id]}
        
        print(f"📄 Generating invoice for Shiprocket Order ID: {shiprocket_order_id}")
        
        invoice_response = requests.post(
            invoice_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if invoice_response.status_code == 200:
            invoice_data = invoice_response.json()
            
            # Get PDF URL
            pdf_url = (
                invoice_data.get("invoice_url") or
                invoice_data.get("url") or
                invoice_data.get("data", {}).get("invoice_url")
            )
            
            if pdf_url:
                print(f"✅ Invoice URL: {pdf_url}\n")
                return RedirectResponse(url=pdf_url)
            
            # Check base64
            pdf_base64 = invoice_data.get("pdf") or invoice_data.get("data", {}).get("pdf")
            if pdf_base64:
                return JSONResponse({
                    "success": True,
                    "pdf_base64": pdf_base64
                })
        
        return JSONResponse({
            "success": False,
            "message": "Invoice generation failed",
            "error": invoice_response.text
        }, status_code=500)
        
    except Exception as e:
        print(f"❌ Invoice Error: {str(e)}")
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
            # ✅ Store real Shiprocket data
            shiprocket_order_id=shipment_result.get("shiprocket_order_id"),
            shipment_id=shipment_result.get("shipment_id"),
            awb_code=shipment_result.get("awb_code") or shipment_result.get("waybill"),
            courier_id=shipment_result.get("courier_id"),
            courier_name=shipment_result.get("courier_name", "Shiprocket"),
            waybill_number=shipment_result.get("awb_code") or shipment_result.get("waybill"),
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
async def track_order(order_id: str, email: str, db: Session = Depends(get_db)):
    """Track order with Shiprocket delivery status - ✅ Updates order status from Shiprocket"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # ✅ Verify email
    if order.shipping_email.lower() != email.lower():
        raise HTTPException(status_code=403, detail="Not authorized to track this order")
    
    delivery = db.query(Delivery).filter(Delivery.order_id == order.id).first()
    
    # ✅ FIRST: Check order status via order details API
    shiprocket_order_status = None
    if order.shiprocket_order_id:
        try:
            print(f"🔍 Checking Shiprocket order status: {order.shiprocket_order_id}")
            order_details = shiprocket_service.get_order_details(order.shiprocket_order_id)
            
            if order_details.get("success"):
                shiprocket_order_status = order_details.get("status", "").upper()
                print(f"📊 Shiprocket order status: '{shiprocket_order_status}'")
                
                # ✅ UPDATE ORDER IF CANCELLED
                if shiprocket_order_status == "CANCELED":
                    if order.order_status != OrderStatus.CANCELLED:
                        print(f"✅ Order CANCELED in Shiprocket → Updating database")
                        order.order_status = OrderStatus.CANCELLED
                        if delivery:
                            delivery.current_status = "CANCELED"
                        db.commit()
                        db.refresh(order)
                        if delivery:
                            db.refresh(delivery)
                        print(f"✅ Order status saved: CANCELED")
        except Exception as e:
            print(f"⚠️ Failed to get order status: {str(e)}")
    
    # ✅ SECOND: Get live tracking from Shiprocket if shipment exists
    live_tracking = None
    if delivery and delivery.shipment_id and order.order_status != OrderStatus.CANCELLED:
        try:
            print(f"🔍 Fetching live tracking for shipment: {delivery.shipment_id}")
            live_tracking = shiprocket_service.track_shipment(delivery.shipment_id)
            
            # ✅ UPDATE ORDER STATUS FROM TRACKING
            if live_tracking.get("success"):
                shiprocket_status = live_tracking.get("current_status", "").lower()
                print(f"📊 Shiprocket tracking status: '{shiprocket_status}'")
                
                status_updated = False
                
                # Check for delivery
                if "delivered" in shiprocket_status:
                    if order.order_status != OrderStatus.DELIVERED:
                        print(f"✅ Updating order: {order.order_status} → DELIVERED")
                        order.order_status = OrderStatus.DELIVERED
                        if delivery:
                            delivery.current_status = "Delivered"
                        status_updated = True
                
                # Check for shipment
                elif any(x in shiprocket_status for x in ["transit", "picked", "dispatched", "out for delivery"]):
                    if order.order_status not in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                        print(f"✅ Updating order: {order.order_status} → SHIPPED")
                        order.order_status = OrderStatus.SHIPPED
                        if delivery:
                            delivery.current_status = shiprocket_status.title()
                        status_updated = True
                
                # Check for processing
                elif "pickup scheduled" in shiprocket_status or "manifest" in shiprocket_status:
                    if order.order_status == OrderStatus.CONFIRMED:
                        print(f"✅ Updating order: {order.order_status} → PROCESSING")
                        order.order_status = OrderStatus.PROCESSING
                        if delivery:
                            delivery.current_status = "Processing"
                        status_updated = True
                
                # Save changes
                if status_updated:
                    db.commit()
                    db.refresh(order)
                    if delivery:
                        db.refresh(delivery)
                    print(f"✅ Order status saved to database")
        except Exception as tracking_error:
            print(f"⚠️ Live tracking failed: {str(tracking_error)}")
            traceback.print_exc()
    
    # Build tracking updates
    tracking_updates = []
    
    # ✅ Add cancellation message if cancelled
    if order.order_status == OrderStatus.CANCELLED:
        tracking_updates.append({
            "status": "Order Cancelled",
            "location": order.shipping_city or "N/A",
            "timestamp": order.updated_at.isoformat() if order.updated_at else datetime.now().isoformat(),
            "description": "Your order has been cancelled. If you paid online, refund will be processed within 5-7 business days."
        })
    
    # Add live tracking history
    if live_tracking and live_tracking.get("tracking_history"):
        for track in live_tracking["tracking_history"]:
            tracking_updates.append({
                "status": track.get("status", "Status Update"),
                "location": track.get("location", ""),
                "timestamp": track.get("date", ""),
                "description": track.get("activity", track.get("status", ""))
            })
    
    # Add delivery tracking history
    if delivery and delivery.tracking_history and not tracking_updates:
        tracking_updates = delivery.tracking_history
    
    # ✅ If no updates, add default
    if not tracking_updates:
        tracking_updates.append({
            "status": order.order_status.value.title(),
            "location": order.shipping_city or "N/A",
            "timestamp": order.created_at.isoformat() if order.created_at else datetime.now().isoformat(),
            "description": f"Order is {order.order_status.value}"
        })
    
    # Build response
    tracking_info = {
        "orderId": order.order_id,
        "status": order.order_status.value,  # ✅ Now reflects live status
        "paymentStatus": order.payment_status.value,
        "estimatedDelivery": order.estimated_delivery,
        "shiprocketOrderId": order.shiprocket_order_id,
        "shipmentId": order.shipment_id,
        "awbCode": order.awb_code,
        "courierId": order.courier_id,
        "waybillNumber": order.waybill_number,
        "trackingUrl": delivery.tracking_url if delivery else None,
        "deliveryStatus": "Cancelled" if order.order_status == OrderStatus.CANCELLED else (live_tracking.get("current_status") if live_tracking else (delivery.current_status if delivery else order.order_status.value.title())),
        "currentLocation": delivery.current_location if delivery else order.shipping_city,
        "courierName": delivery.courier_name if delivery else None,
        "trackingUpdates": tracking_updates,
        "liveTracking": live_tracking
    }
    
    print(f"✅ Final tracking response: status={tracking_info['status']}, deliveryStatus={tracking_info['deliveryStatus']}")
    
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


# Replace the /calculate endpoint at the END of orders.py

@router.post("/calculate")
async def calculate_order_total(data: dict):
    """Calculate order total including Shiprocket shipping - MUST match /create"""
    try:
        items = data.get("items", [])
        shipping_address = data.get("shipping_address", {})
        payment_method = data.get("payment_method", "cod")
        
        # ✅ Calculate subtotal (SAME as /create)
        subtotal = sum(item["price"] * item["quantity"] for item in items)
        
        # ✅ Calculate weight (SAME as /create)
        total_weight = sum(item["quantity"] * 1.0 for item in items)
        
        # ✅ Determine COD (SAME as /create)
        is_cod = payment_method == "cod"
        
        # ✅ ADD DETAILED LOGGING
        print(f"\n{'='*80}")
        print(f"🛒 CART CALCULATION (/calculate endpoint)")
        print(f"   Items Count: {len(items)}")
        print(f"   Subtotal: ₹{subtotal}")
        print(f"   Weight: {total_weight}kg")
        print(f"   Pincode: {shipping_address.get('pincode')}")
        print(f"   Payment Method: {payment_method}")
        print(f"   Is COD: {is_cod}")
        print(f"   Debug Mode: {settings.debug}")
        print(f"{'='*80}\n")
        
        # ✅ Calculate shipping (SAME function as /create)
        shipping_cost = calculate_shipping_cost(
            shipping_address.get("pincode", ""), 
            total_weight,
            subtotal,
            is_cod
        )
        
        total = subtotal + shipping_cost
        
        # ✅ LOG FINAL RESULT
        print(f"✅ CART CALCULATION RESULT:")
        print(f"   Subtotal: ₹{subtotal}")
        print(f"   Shipping: ₹{shipping_cost}")
        print(f"   Total: ₹{total}")
        print(f"   Free Shipping: {subtotal >= 999}")
        print(f"{'='*80}\n")
        
        return {
            "subtotal": round(subtotal, 2),
            "shippingCost": round(shipping_cost, 2),
            "total": round(total, 2),
            "freeShippingEligible": subtotal >= 999
        }
        
    except Exception as e:
        print(f"❌ Calculate endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))