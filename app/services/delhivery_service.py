# backend/app/services/delhivery_service.py
import requests
import os
from typing import Dict, Optional
from datetime import datetime, timedelta

class DelhiveryService:
    """Delhivery API Integration Service"""
    
    BASE_URL = "https://track.delhivery.com/api"
    STAGING_URL = "https://staging-express.delhivery.com/api"
    
    def __init__(self):
        self.api_key = os.getenv("DELHIVERY_API_KEY")
        self.debug = os.getenv("DEBUG", "True") == "True"
        self.base_url = self.STAGING_URL if self.debug else self.BASE_URL
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        } if self.api_key else {}
    
    def create_shipment(self, order_data: dict) -> Dict:
        """
        Create shipment with Delhivery
        Args:
            order_data: Dictionary containing all order details
        Returns:
            Dict with waybill and shipment details
        """
        try:
            # ✅ Development/Testing mode - skip actual API call
            if self.debug or not self.api_key:
                print(f"🔧 [DEV MODE] Creating mock shipment for order {order_data.get('order_id')}")
                return self._create_mock_shipment(order_data.get('order_id', 'TEST'))
            
            # Production mode - actual API call
            url = f"{self.base_url}/cmu/create.json"
            
            # Prepare products list
            products_desc = order_data.get("products_desc", "Cold-Pressed Oils")
            
            # Warehouse details
            warehouse_pincode = os.getenv("WAREHOUSE_PINCODE", "110001")
            warehouse_city = os.getenv("WAREHOUSE_CITY", "Delhi")
            warehouse_phone = os.getenv("WAREHOUSE_PHONE", "9876543210")
            warehouse_address = os.getenv("WAREHOUSE_ADDRESS", "Pure & Desi Warehouse")
            warehouse_state = os.getenv("WAREHOUSE_STATE", "Delhi")
            company_name = os.getenv("COMPANY_NAME", "Pure & Desi")
            gst_number = os.getenv("GST_NUMBER", "")
            
            shipment_data = {
                "shipments": [{
                    "name": order_data.get("shipping_name"),
                    "add": order_data.get("shipping_address"),
                    "pin": order_data.get("shipping_pincode"),
                    "city": order_data.get("shipping_city"),
                    "state": order_data.get("shipping_state"),
                    "country": "India",
                    "phone": order_data.get("shipping_phone"),
                    "order": order_data.get("order_id"),
                    "payment_mode": "COD" if order_data.get("payment_method") == "cod" else "Prepaid",
                    "return_pin": warehouse_pincode,
                    "return_city": warehouse_city,
                    "return_phone": warehouse_phone,
                    "return_add": warehouse_address,
                    "return_state": warehouse_state,
                    "return_country": "India",
                    "products_desc": products_desc,
                    "hsn_code": "",
                    "cod_amount": str(order_data.get("total", 0)) if order_data.get("payment_method") == "cod" else "0",
                    "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_amount": str(order_data.get("total", 0)),
                    "seller_add": warehouse_address,
                    "seller_name": company_name,
                    "seller_inv": order_data.get("order_id"),
                    "quantity": str(order_data.get("total_quantity", 1)),
                    "waybill": "",
                    "shipment_width": "15",
                    "shipment_height": "10",
                    "weight": str(order_data.get("weight", 1)),
                    "seller_gst_tin": gst_number,
                    "shipping_mode": "Surface",
                    "address_type": "home"
                }],
                "pickup_location": {
                    "name": os.getenv("WAREHOUSE_NAME", "Pure & Desi Warehouse")
                }
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=shipment_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    waybill = data.get("packages", [{}])[0].get("waybill", "")
                    
                    return {
                        "success": True,
                        "waybill": waybill,
                        "shipment_id": data.get("packages", [{}])[0].get("refnum", ""),
                        "tracking_url": f"https://www.delhivery.com/track/package/{waybill}",
                        "estimated_delivery": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                    }
                else:
                    print(f"⚠️ Delhivery API Error: {data.get('remark', 'Unknown error')}")
                    return self._create_mock_shipment(order_data.get('order_id', 'TEST'))
            else:
                print(f"⚠️ Delhivery API HTTP Error: {response.status_code}")
                return self._create_mock_shipment(order_data.get('order_id', 'TEST'))
                
        except Exception as e:
            print(f"❌ Shipment creation error: {str(e)}")
            return self._create_mock_shipment(order_data.get('order_id', 'TEST'))
    
    def _create_mock_shipment(self, order_id: str) -> Dict:
        """Create mock shipment for development/testing"""
        waybill = f"PDEL{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        print(f"✅ Mock shipment created: {waybill}")
        
        return {
            "success": True,
            "waybill": waybill,
            "shipment_id": f"SHIP{order_id}",
            "tracking_url": f"https://www.delhivery.com/track/package/{waybill}",
            "estimated_delivery": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "mock": True
        }
    
    def track_shipment(self, waybill: str) -> Dict:
        """Track shipment by waybill number"""
        try:
            # Development mode
            if self.debug or not self.api_key:
                return self._mock_tracking(waybill)
            
            url = f"{self.base_url}/v1/packages/json/"
            params = {
                "waybill": waybill,
                "verbose": "1"
            }
            
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("ShipmentData"):
                    shipment = data["ShipmentData"][0]["Shipment"]
                    scans = shipment.get("Scans", [])
                    
                    return {
                        "waybill": waybill,
                        "status": shipment.get("Status", {}).get("Status", "Unknown"),
                        "current_location": scans[0].get("ScannedLocation", "") if scans else "",
                        "destination": shipment.get("Destination", ""),
                        "estimated_delivery": shipment.get("ExpectedDeliveryDate", ""),
                        "scans": [
                            {
                                "date": scan.get("ScanDateTime", ""),
                                "location": scan.get("ScannedLocation", ""),
                                "status": scan.get("Scan", ""),
                                "description": scan.get("Instructions", "")
                            }
                            for scan in scans
                        ]
                    }
                else:
                    return self._mock_tracking(waybill)
            else:
                return self._mock_tracking(waybill)
                
        except Exception as e:
            print(f"Tracking error: {str(e)}")
            return self._mock_tracking(waybill)
    
    def _mock_tracking(self, waybill: str) -> Dict:
        """Mock tracking data for testing"""
        return {
            "waybill": waybill,
            "status": "In Transit",
            "current_location": "Delhi Hub",
            "destination": "Customer Location",
            "estimated_delivery": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "scans": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "location": "Delhi",
                    "status": "Picked Up",
                    "description": "Shipment picked up"
                },
                {
                    "date": (datetime.now() + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"),
                    "location": "Delhi Hub",
                    "status": "In Transit",
                    "description": "Shipment in transit"
                }
            ],
            "mock": True
        }
    
    def cancel_shipment(self, waybill: str) -> Dict:
        """Cancel shipment"""
        try:
            if self.debug or not self.api_key:
                print(f"🔧 [DEV MODE] Cancelling shipment: {waybill}")
                return {"success": True, "mock": True}
            
            # Add actual cancellation API call here
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
delhivery_service = DelhiveryService()