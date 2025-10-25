import requests
from typing import Dict, Optional, List
from datetime import datetime
import random
from app.config.settings import settings

class WhatsAppService:
    """WhatsApp Business API Integration Service"""
    
    # WhatsApp Business API endpoints
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self):
        self.api_token = settings.whatsapp_api_token
        self.phone_number_id = settings.whatsapp_phone_number_id or ""
        self.business_phone = settings.whatsapp_business_phone or "+919876543210"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # OTP storage (Use Redis in production)
        self.otp_storage = {}
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number to international format"""
        # Remove all non-numeric characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Add country code if not present
        if not phone.startswith('91') and len(phone) == 10:
            phone = f"91{phone}"
        
        return phone
    
    def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Send WhatsApp template message
        
        Args:
            phone_number: Recipient phone number
            template_name: Template name from WhatsApp Business
            language_code: Language code (en, hi, etc.)
            components: Template components/parameters
            
        Returns:
            Dict with send status
        """
        try:
            if not self.api_token or self.api_token == "your_token_here":
                return self._mock_send(phone_number, "Template message")
            
            phone = self._format_phone(phone_number)
            
            url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id", ""),
                    "phone_number": phone_number
                }
            else:
                return self._mock_send(phone_number, f"Template: {template_name}")
                
        except Exception as e:
            print(f"WhatsApp template send error: {str(e)}")
            return self._mock_send(phone_number, f"Template: {template_name}")
    
    def send_order_confirmation(
        self,
        phone_number: str,
        order_id: str,
        customer_name: str,
        total_amount: float,
        items_count: int
    ) -> Dict:
        """Send order confirmation message"""
        try:
            phone = self._format_phone(phone_number)
            
            # Template components
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": customer_name},
                        {"type": "text", "text": order_id},
                        {"type": "text", "text": str(items_count)},
                        {"type": "text", "text": f"₹{total_amount:.2f}"}
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {"type": "text", "text": order_id}
                    ]
                }
            ]
            
            return self.send_template_message(
                phone_number=phone,
                template_name="order_confirmation",
                components=components
            )
            
        except Exception as e:
            print(f"Order confirmation error: {str(e)}")
            return self._mock_send(phone_number, f"Order {order_id} confirmed")
    
    def send_shipping_update(
        self,
        phone_number: str,
        order_id: str,
        waybill: str,
        courier_name: str,
        estimated_delivery: str
    ) -> Dict:
        """Send shipping update message"""
        try:
            phone = self._format_phone(phone_number)
            
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": order_id},
                        {"type": "text", "text": waybill},
                        {"type": "text", "text": courier_name},
                        {"type": "text", "text": estimated_delivery}
                    ]
                }
            ]
            
            return self.send_template_message(
                phone_number=phone,
                template_name="shipping_update",
                components=components
            )
            
        except Exception as e:
            print(f"Shipping update error: {str(e)}")
            return self._mock_send(phone_number, f"Order {order_id} shipped")
    
    def send_delivery_notification(
        self,
        phone_number: str,
        order_id: str,
        customer_name: str
    ) -> Dict:
        """Send delivery notification"""
        try:
            phone = self._format_phone(phone_number)
            
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": customer_name},
                        {"type": "text", "text": order_id}
                    ]
                }
            ]
            
            return self.send_template_message(
                phone_number=phone,
                template_name="delivery_notification",
                components=components
            )
            
        except Exception as e:
            print(f"Delivery notification error: {str(e)}")
            return self._mock_send(phone_number, f"Order {order_id} delivered")
    
    def send_otp(self, phone_number: str) -> Dict:
        """
        Send OTP for verification
        
        Args:
            phone_number: Phone number
            
        Returns:
            Dict with OTP send status
        """
        try:
            phone = self._format_phone(phone_number)
            
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Store OTP with expiry (10 minutes)
            self.otp_storage[phone] = {
                "otp": otp,
                "created_at": datetime.now(),
                "expires_in": 600  # 10 minutes
            }
            
            # Send OTP via template
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": otp}
                    ]
                }
            ]
            
            result = self.send_template_message(
                phone_number=phone,
                template_name="otp_verification",
                components=components
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": "OTP sent successfully",
                    "phone_number": phone_number,
                    "expires_in": 600
                }
            else:
                return result
                
        except Exception as e:
            print(f"OTP send error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_otp(self, phone_number: str, otp: str) -> Dict:
        """
        Verify OTP
        
        Args:
            phone_number: Phone number
            otp: OTP to verify
            
        Returns:
            Dict with verification status
        """
        try:
            phone = self._format_phone(phone_number)
            
            if phone not in self.otp_storage:
                return {
                    "success": False,
                    "verified": False,
                    "error": "OTP not found or expired"
                }
            
            stored_data = self.otp_storage[phone]
            stored_otp = stored_data["otp"]
            created_at = stored_data["created_at"]
            expires_in = stored_data["expires_in"]
            
            # Check expiry
            elapsed = (datetime.now() - created_at).total_seconds()
            if elapsed > expires_in:
                del self.otp_storage[phone]
                return {
                    "success": False,
                    "verified": False,
                    "error": "OTP expired"
                }
            
            # Verify OTP
            if stored_otp == otp:
                del self.otp_storage[phone]
                return {
                    "success": True,
                    "verified": True,
                    "phone_number": phone_number
                }
            else:
                return {
                    "success": False,
                    "verified": False,
                    "error": "Invalid OTP"
                }
                
        except Exception as e:
            print(f"OTP verification error: {str(e)}")
            return {
                "success": False,
                "verified": False,
                "error": str(e)
            }
    
    def send_custom_message(
        self,
        phone_number: str,
        message: str
    ) -> Dict:
        """
        Send custom text message (requires approved template)
        Note: Direct text messages need WhatsApp Business approval
        
        Args:
            phone_number: Recipient phone number
            message: Message text
            
        Returns:
            Dict with send status
        """
        try:
            if not self.api_token or self.api_token == "your_token_here":
                return self._mock_send(phone_number, message)
            
            phone = self._format_phone(phone_number)
            
            url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id", ""),
                    "phone_number": phone_number
                }
            else:
                return self._mock_send(phone_number, message)
                
        except Exception as e:
            print(f"Custom message send error: {str(e)}")
            return self._mock_send(phone_number, message)
    
    def _mock_send(self, phone_number: str, message_type: str) -> Dict:
        """Mock message sending for testing"""
        print(f"📱 [MOCK] WhatsApp to {phone_number}: {message_type}")
        
        return {
            "success": True,
            "message_id": f"wamid.{int(datetime.now().timestamp())}",
            "phone_number": phone_number,
            "mock": True
        }
    
    def get_business_info(self) -> Dict:
        """Get WhatsApp Business profile info"""
        return {
            "business_name": "Pure & Desi",
            "business_phone": self.business_phone,
            "description": "Premium Cold-Pressed Oils",
            "category": "Food & Beverage",
            "website": "https://thepureanddesi.com"
        }


# Create singleton instance
whatsapp_service = WhatsAppService()