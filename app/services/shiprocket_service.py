# backend/app/services/shiprocket_service.py
import requests
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from app.config.settings import settings

class ShiprocketService:
    """Shiprocket API Integration Service - Production Ready"""
    
    BASE_URL = "https://apiv2.shiprocket.in/v1/external"
    
    def __init__(self):
        self.email = settings.shiprocket_email
        self.password = settings.shiprocket_password
        self.debug = settings.debug
        self.token = None
        self.token_expiry = None
        
        print(f"🚀 ShiprocketService initialized")
        print(f"   Debug Mode: {self.debug}")
        print(f"   Warehouse: {settings.warehouse_pincode}")
        
        # Auto-login on initialization (only if not debug)
        if not self.debug and self.email and self.password:
            self._login()
    
    # ✅ NEW: Add phone formatting function
    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number for Shiprocket API
        Shiprocket expects 10-digit phone without country code
        
        Examples:
        - +918887948909 → 8887948909
        - 918887948909 → 8887948909
        - 08887948909 → 8887948909
        - 8887948909 → 8887948909
        """
        # Remove all non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Remove country code (91) if present
        if phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]
        
        # Remove leading zero if present
        if phone.startswith('0') and len(phone) == 11:
            phone = phone[1:]
        
        # Validate 10-digit number
        if len(phone) != 10:
            print(f"⚠️ Invalid phone: {phone} (length: {len(phone)})")
            # Return as is if can't format properly
            return phone
        
        print(f"📱 Phone formatted: {phone}")
        return phone
    
    def _login(self) -> bool:
        """Login to Shiprocket and get auth token"""
        try:
            url = f"{self.BASE_URL}/auth/login"
            
            # Strip any whitespace/quotes
            email = self.email.strip().strip('"').strip("'")
            password = self.password.strip().strip('"').strip("'")
            
            payload = {
                "email": email,
                "password": password
            }
            
            print(f"🔐 Attempting Shiprocket login...")
            print(f"   Email: {email}")
            print(f"   Password length: {len(password)} chars")
            
            response = requests.post(url, json=payload, timeout=30)
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.token_expiry = datetime.now() + timedelta(days=7)
                print(f"✅ Shiprocket login successful")
                print(f"   Token: {self.token[:50]}...")
                return True
            else:
                print(f"❌ Shiprocket login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Shiprocket login error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_headers(self) -> Dict:
        """Get request headers with auth token"""
        if not self.token or datetime.now() >= self.token_expiry:
            self._login()
        
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def check_pincode_serviceability(self, pincode: str, cod: bool = True) -> Dict:
        """Check if delivery is available for pincode"""
        try:
            print(f"\n{'='*60}")
            print(f"🔍 CHECKING PINCODE SERVICEABILITY")
            print(f"📍 Pincode: {pincode}")
            print(f"💰 COD: {cod}")
            print(f"{'='*60}\n")
            
            if self.debug:
                print("🔧 Debug mode - using mock data")
                return self._mock_serviceability(pincode)
            
            url = f"{self.BASE_URL}/courier/serviceability"
            params = {
                "pickup_postcode": settings.warehouse_pincode,
                "delivery_postcode": pincode,
                "cod": 1 if cod else 0,
                "weight": "1"
            }
            
            print(f"📡 Calling Shiprocket API...")
            print(f"Params: {params}")
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                courier_data = data.get("data", {})
                available_couriers = courier_data.get("available_courier_companies", [])
                
                if available_couriers:
                    # ✅ NEW: Prefer Amazon Shipping Surface
                    selected_courier = None
                    
                    # Try to find Amazon Shipping Surface
                    for courier in available_couriers:
                        courier_name = courier.get("courier_name", "").lower()
                        if "amazon shipping surface" in courier_name:
                            selected_courier = courier
                            print(f"✅ Found preferred courier: Amazon Shipping Surface")
                            break
                    
                    # Fallback: If Amazon not available, use cheapest
                    if not selected_courier:
                        print(f"⚠️ Amazon Shipping not available, using cheapest")
                        def get_rate(c):
                            try:
                                rate = c.get("rate") or c.get("freight_charge") or c.get("total_charge")
                                return float(rate) if rate is not None else 999999
                            except:
                                return 999999
                        
                        selected_courier = min(available_couriers, key=get_rate)
                    
                    print(f"🚚 Selected courier: {selected_courier.get('courier_name', 'Unknown')}")
                    
                    # ✅ Extract data from selected courier
                    result = {
                        "serviceable": True,
                        "pincode": pincode,
                        "city": selected_courier.get("city", ""),
                        "state": selected_courier.get("state", ""),
                        "cod_available": selected_courier.get("cod", 1) == 1,
                        "prepaid_available": True,
                        "shipping_charge": float(selected_courier.get("rate") or selected_courier.get("freight_charge") or 50),
                        "cod_charges": float(selected_courier.get("cod_charges", 0)),
                        "estimated_days": selected_courier.get("etd", "3-5 days"),
                        "courier_name": selected_courier.get("courier_name", ""),
                        "courier_id": selected_courier.get("courier_company_id"),
                        "available_couriers": len(available_couriers)
                    }
                    
                    print(f"✅ Pincode is serviceable")
                    print(f"📍 City: {result['city']}")
                    print(f"📍 State: {result['state']}")
                    print(f"💰 Shipping: ₹{result['shipping_charge']}")
                    print(f"🚚 Courier: {result['courier_name']}")
                    print(f"⏱️  ETA: {result['estimated_days']}")
                    
                    return result
            
            print("❌ Pincode not serviceable or API error")
            return {
                "serviceable": False, 
                "pincode": pincode,
                "error": "No courier available for this pincode"
            }
            
        except Exception as e:
            print(f"❌ Serviceability check error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "serviceable": False, 
                "pincode": pincode,
                "error": str(e)
            }


   
    def _mock_serviceability(self, pincode: str) -> Dict:
        """Mock serviceability check for development"""
        pincode_database = {
            # Uttar Pradesh
            "212": {"city": "Fatehpur", "state": "Uttar Pradesh"},
            "226": {"city": "Lucknow", "state": "Uttar Pradesh"},
            "281": {"city": "Mathura", "state": "Uttar Pradesh"},
            "201": {"city": "Ghaziabad", "state": "Uttar Pradesh"},
            "211": {"city": "Prayagraj", "state": "Uttar Pradesh"},
            "221": {"city": "Varanasi", "state": "Uttar Pradesh"},
            
            # Delhi NCR
            "110": {"city": "Delhi", "state": "Delhi"},
            "121": {"city": "Gurugram", "state": "Haryana"},
            "122": {"city": "Gurugram", "state": "Haryana"},
            "201": {"city": "Noida", "state": "Uttar Pradesh"},
            
            # Maharashtra
            "400": {"city": "Mumbai", "state": "Maharashtra"},
            "401": {"city": "Thane", "state": "Maharashtra"},
            "411": {"city": "Pune", "state": "Maharashtra"},
            "440": {"city": "Nagpur", "state": "Maharashtra"},
            "431": {"city": "Aurangabad", "state": "Maharashtra"},
            
            # Karnataka
            "560": {"city": "Bangalore", "state": "Karnataka"},
            "570": {"city": "Mysore", "state": "Karnataka"},
            "580": {"city": "Hubli", "state": "Karnataka"},
            
            # Tamil Nadu
            "600": {"city": "Chennai", "state": "Tamil Nadu"},
            "641": {"city": "Coimbatore", "state": "Tamil Nadu"},
            "625": {"city": "Madurai", "state": "Tamil Nadu"},
            
            # West Bengal
            "700": {"city": "Kolkata", "state": "West Bengal"},
            
            # Telangana
            "500": {"city": "Hyderabad", "state": "Telangana"},
            
            # Gujarat
            "380": {"city": "Ahmedabad", "state": "Gujarat"},
            "395": {"city": "Surat", "state": "Gujarat"},
            "390": {"city": "Vadodara", "state": "Gujarat"},
            
            # Rajasthan
            "302": {"city": "Jaipur", "state": "Rajasthan"},
            "303": {"city": "Jaipur", "state": "Rajasthan"},
            "324": {"city": "Kota", "state": "Rajasthan"},
            
            # Madhya Pradesh
            "452": {"city": "Indore", "state": "Madhya Pradesh"},
            "462": {"city": "Bhopal", "state": "Madhya Pradesh"},
            
            # Kerala
            "682": {"city": "Kochi", "state": "Kerala"},
            "695": {"city": "Thiruvananthapuram", "state": "Kerala"},
            
            # Punjab
            "141": {"city": "Ludhiana", "state": "Punjab"},
            "160": {"city": "Chandigarh", "state": "Chandigarh"},
            
            # Other states
            "751": {"city": "Bhubaneswar", "state": "Odisha"},
            "800": {"city": "Patna", "state": "Bihar"},
        }
        
        prefix = pincode[:3]
        location = pincode_database.get(prefix, {"city": "Unknown", "state": "Unknown"})
        
        # Metro cities get better rates
        metro_cities = ["110", "400", "560", "600", "700", "500"]
        is_metro = prefix in metro_cities
        
        result = {
            "serviceable": True,
            "pincode": pincode,
            "city": location["city"],
            "state": location["state"],
            "cod_available": True,
            "estimated_days": "3-5 days" if is_metro else "5-7 days",
            "shipping_charge": 50 if is_metro else 70,
            "courier_name": "Standard Delivery",
            "mock": True
        }
        
        print(f"✅ Mock result: {result}")
        return result
    
    def calculate_shipping_charges(self, pincode: str, weight: float, cod_amount: float = 0) -> Dict:
        """Calculate shipping charges based on weight and pincode"""
        try:
            print(f"\n{'='*60}")
            print(f"💰 CALCULATING SHIPPING CHARGES")
            print(f"📍 Pincode: {pincode}")
            print(f"⚖️  Weight: {weight}kg")
            print(f"💵 COD Amount: ₹{cod_amount}")
            print(f"{'='*60}\n")
            
            if self.debug:
                print("🔧 Debug mode - using mock calculation")
                return self._mock_shipping_charges(pincode, weight, cod_amount)
            
            url = f"{self.BASE_URL}/courier/serviceability"
            params = {
                "pickup_postcode": settings.warehouse_pincode,
                "delivery_postcode": pincode,
                "cod": 1 if cod_amount > 0 else 0,
                "weight": str(weight)
            }
            
            print(f"📡 Calling Shiprocket API...")
            print(f"Params: {params}")
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                courier_data = data.get("data", {})
                available_couriers = courier_data.get("available_courier_companies", [])
                
                print(f"📦 Available couriers: {len(available_couriers)}")
                
                if available_couriers:
                    # ✅ NEW: Prefer Amazon Shipping Surface (same logic as check_pincode)
                    selected_courier = None
                    
                    # Try to find Amazon Shipping Surface
                    for courier in available_couriers:
                        courier_name = courier.get("courier_name", "").lower()
                        if "amazon shipping surface" in courier_name:
                            selected_courier = courier
                            print(f"✅ Found preferred courier: Amazon Shipping Surface")
                            break
                    
                    # Fallback: If Amazon not available, use cheapest
                    if not selected_courier:
                        print(f"⚠️ Amazon Shipping not available, using cheapest")
                        def get_rate(c):
                            try:
                                rate = c.get("rate") or c.get("freight_charge") or c.get("total_charge")
                                return float(rate) if rate is not None else 999999
                            except:
                                return 999999
                        
                        selected_courier = min(available_couriers, key=get_rate)
                    
                    print(f"🚚 Selected courier: {selected_courier.get('courier_name', 'Unknown')}")
                    
                    # ✅ Extract charges from selected courier
                    shipping_charge = float(selected_courier.get("rate") or selected_courier.get("freight_charge") or selected_courier.get("total_charge") or 50)
                    cod_charge = float(selected_courier.get("cod_charges") or selected_courier.get("cod_charge") or 0) if cod_amount > 0 else 0
                    
                    # ✅ Get estimated days properly
                    estimated_days = selected_courier.get('etd', '3-5')
                    if estimated_days and isinstance(estimated_days, str):
                        if 'days' not in estimated_days.lower():
                            estimated_days = f"{estimated_days} days"
                    else:
                        estimated_days = "3-5 days"
                    
                    result = {
                        "pincode": pincode,
                        "weight": weight,
                        "shipping_charge": shipping_charge,
                        "cod_charge": cod_charge,
                        "total_charge": shipping_charge + cod_charge,
                        "estimated_days": estimated_days,
                        "courier_name": selected_courier.get("courier_name", "Shiprocket")
                    }
                    
                    print(f"✅ Calculation result:")
                    print(f"   🚚 Courier: {result['courier_name']}")
                    print(f"   💰 Shipping: ₹{result['shipping_charge']}")
                    print(f"   💵 COD: ₹{result['cod_charge']}")
                    print(f"   💵 Total: ₹{result['total_charge']}")
                    print(f"   ⏱️  ETA: {result['estimated_days']}\n")
                    
                    return result
            
            print("⚠️ API error or no couriers, using mock")
            return self._mock_shipping_charges(pincode, weight, cod_amount)
            
        except Exception as e:
            print(f"❌ Shipping calculation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._mock_shipping_charges(pincode, weight, cod_amount)

    def _mock_shipping_charges(self, pincode: str, weight: float, cod_amount: float) -> Dict:
        """Mock shipping charges with proper weight-based calculation"""
        print(f"🔧 Calculating mock charges...")
        
        metro_cities = ["110", "400", "560", "600", "700", "500"]
        is_metro = pincode[:3] in metro_cities
        
        # ✅ WEIGHT-BASED CALCULATION
        if weight <= 0.5:
            base_charge = 35 if is_metro else 45
        elif weight <= 1.0:
            base_charge = 50 if is_metro else 65
        elif weight <= 2.0:
            base_charge = 70 if is_metro else 90
        elif weight <= 3.0:
            base_charge = 90 if is_metro else 115
        elif weight <= 5.0:
            base_charge = 120 if is_metro else 150
        else:
            # Above 5kg: ₹20 per additional kg
            extra_weight = weight - 5
            base_charge = (120 if is_metro else 150) + (extra_weight * 20)
        
        # COD charges
        cod_charge = 40 if cod_amount > 0 else 0
        
        total_charge = base_charge + cod_charge
        
        result = {
            "pincode": pincode,
            "weight": weight,
            "shipping_charge": base_charge,
            "cod_charge": cod_charge,
            "total_charge": total_charge,
            "estimated_days": "3-5 days" if is_metro else "5-7 days",
            "mock": True
        }
        
        print(f"✅ Mock calculation:")
        print(f"   Base (weight-based): ₹{base_charge}")
        print(f"   COD charges: ₹{cod_charge}")
        print(f"   Total: ₹{total_charge}\n")
        
        return result
    
    def create_shipment(self, order_data: dict) -> Dict:
        """Create shipment with Shiprocket"""
        try:
            if self.debug:
                print(f"🔧 [DEV MODE] Creating mock shipment for order {order_data.get('order_id')}")
                return self._create_mock_shipment(order_data.get('order_id', 'TEST'))
            
            url = f"{self.BASE_URL}/orders/create/adhoc"
            
            # ✅ FORMAT PHONE NUMBERS
            shipping_phone = self.format_phone_number(order_data.get("shipping_phone", ""))
            
            # Prepare shipment payload
            payload = {
                "order_id": order_data.get("order_id"),
                "order_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "pickup_location": settings.warehouse_name,
                "channel_id": settings.shiprocket_channel_id or "",
                "comment": "Order from Pure & Desi",
                "billing_customer_name": order_data.get("shipping_name"),
                "billing_last_name": "",
                "billing_address": order_data.get("shipping_address"),
                "billing_address_2": "",
                "billing_city": order_data.get("shipping_city"),
                "billing_pincode": order_data.get("shipping_pincode"),
                "billing_state": order_data.get("shipping_state"),
                "billing_country": "India",
                "billing_email": order_data.get("shipping_email", "customer@pureanddesi.com"),
                "billing_phone": shipping_phone,  # ✅ USE FORMATTED PHONE
                "shipping_is_billing": True,
                "order_items": [{
                    "name": item.get("product_name", "Cold-Pressed Oil"),
                    "sku": f"PROD{item.get('product_id', '001')}",
                    "units": item.get("quantity", 1),
                    "selling_price": str(item.get("price", 0)),
                    "discount": "",
                    "tax": "",
                    "hsn": ""
                } for item in order_data.get("items", [])],
                "payment_method": "COD" if order_data.get("payment_method") == "cod" else "Prepaid",
                "shipping_charges": str(order_data.get("shipping_cost", 0)),
                "giftwrap_charges": "0",
                "transaction_charges": "0",
                "total_discount": "0",
                "sub_total": str(order_data.get("subtotal", 0)),
                "length": 15,
                "breadth": 15,
                "height": 10,
                "weight": order_data.get("weight", 1)
            }
            
            print(f"📦 Creating shipment...")
            print(f"   Phone: {shipping_phone}")  # ✅ Debug formatted phone
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # ✅ EXTRACT REAL SHIPROCKET DATA
                if data.get("order_id"):
                    result = {
                        "success": True,
                        "shiprocket_order_id": str(data.get("order_id")),  # ✅ Real Shiprocket order ID
                        "shipment_id": str(data.get("shipment_id")),      # ✅ Real shipment ID
                        "awb_code": data.get("awb_code", ""),              # ✅ Real AWB code
                        "courier_id": data.get("courier_id"),              # ✅ Real courier ID
                        "courier_name": data.get("courier_name", ""),      # ✅ Real courier name
                        "tracking_url": f"https://shiprocket.co/tracking/{data.get('shipment_id', '')}",
                        "estimated_delivery": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
                    }
                    print(f"✅ Shipment created successfully!")
                    print(f"   Shiprocket Order ID: {result['shiprocket_order_id']}")
                    print(f"   Shipment ID: {result['shipment_id']}")
                    print(f"   AWB Code: {result['awb_code']}")
                    print(f"   Courier: {result['courier_name']}")
                    return result
            
            # ✅ PROPER ERROR HANDLING - NO FAKE DATA
            print(f"❌ Shiprocket API Error: {response.text}")
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
            
        except Exception as e:
            print(f"❌ Shipment creation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_mock_shipment(self, order_id: str) -> Dict:
        """Create mock shipment for development"""
        waybill = f"SR{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "success": True,
            "waybill": waybill,
            "shipment_id": f"SHIP{order_id}",
            "awb_code": waybill,
            "tracking_url": f"https://shiprocket.co/tracking/{waybill}",
            "courier_name": "Shiprocket Express",
            "estimated_delivery": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "mock": True
        }
    
    
    def get_order_details(self, shiprocket_order_id: str) -> Dict:
        """Get order details from Shiprocket"""
        try:
            if self.debug:
                return {"success": False, "message": "Debug mode"}
            
            url = f"{self.BASE_URL}/orders/show/{shiprocket_order_id}"
            
            print(f"🔍 Getting order details: {shiprocket_order_id}")
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # ✅ Handle different formats
                if isinstance(data, dict) and "data" in data:
                    order_data = data["data"]
                else:
                    order_data = data
                
                # Get status
                status = order_data.get("status", "")
                
                # ✅ CORRECT: Check type FIRST, then extract
                shipments = order_data.get("shipments")
                shipment_status = ""
                
                if shipments:
                    print(f"📦 Shipments type: {type(shipments)}")
                    
                    # ✅ Check if LIST
                    if isinstance(shipments, list) and len(shipments) > 0:
                        shipment_status = shipments[0].get("status", "")
                        print(f"📦 Shipment status (from list): '{shipment_status}'")
                    # ✅ Check if DICT
                    elif isinstance(shipments, dict):
                        shipment_status = shipments.get("status", "")
                        print(f"📦 Shipment status (from dict): '{shipment_status}'")
                
                result = {
                    "success": True,
                    "order_id": shiprocket_order_id,
                    "status": status,
                    "shipment_status": shipment_status,
                    "order_data": order_data
                }
                
                print(f"✅ Order status: '{status}'")
                if shipment_status:
                    print(f"   Shipment status: '{shipment_status}'")
                
                return result
            
            return {"success": False, "error": response.text}
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    

    def track_shipment(self, shipment_id: str) -> Dict:
        """Track shipment by ID"""
        try:
            if self.debug:
                return self._mock_tracking(shipment_id)
            
            url = f"{self.BASE_URL}/courier/track/shipment/{shipment_id}"
            
            print(f"🔍 Tracking shipment: {shipment_id}")
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                tracking_data = data.get("tracking_data", {})
                
                result = {
                    "success": True,
                    "shipment_id": shipment_id,
                    "current_status": tracking_data.get("shipment_status", ""),
                    "tracking_history": tracking_data.get("shipment_track", []),
                    "estimated_delivery": tracking_data.get("edd", "")
                }
                
                print(f"✅ Tracking result: {result['current_status']}")
                return result
            
            return self._mock_tracking(shipment_id)
            
        except Exception as e:
            print(f"❌ Tracking error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._mock_tracking(shipment_id)
    
    def _mock_tracking(self, shipment_id: str) -> Dict:
        """Mock tracking data"""
        return {
            "success": True,
            "shipment_id": shipment_id,
            "current_status": "In Transit",
            "tracking_history": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "status": "Order Placed",
                    "location": settings.warehouse_city
                }
            ],
            "estimated_delivery": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "mock": True
        }
    
    def generate_invoice(self, shipment_id: str) -> Dict:
        """Generate invoice for a shipment"""
        try:
            if self.debug:
                return {
                    "success": False,
                    "message": "Invoice generation not available in debug mode"
                }
            
            url = f"{self.BASE_URL}/orders/print/invoice"
            
            payload = {
                "ids": [shipment_id]
            }
            
            print(f"📄 Generating invoice for shipment: {shipment_id}")
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("invoice_url"):
                    return {
                        "success": True,
                        "invoice_url": data.get("invoice_url")
                    }
            
            return {
                "success": False,
                "message": "Failed to generate invoice",
                "error": response.text
            }
            
        except Exception as e:
            print(f"❌ Invoice generation error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
shiprocket_service = ShiprocketService()