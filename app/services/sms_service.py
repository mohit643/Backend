# backend/services/sms_service.py
import requests
import os
from typing import Dict
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class SMSService:
    """SMS Service for sending OTP and notifications via various providers"""
    
    def __init__(self):
        # SMS Provider Configuration (MSG91, Twilio, etc.)
        self.provider = os.getenv('SMS_PROVIDER', 'MSG91')
        self.api_key = os.getenv('SMS_API_KEY', '')
        self.sender_id = os.getenv('SMS_SENDER_ID', 'PURDSI')
        self.template_id = os.getenv('SMS_TEMPLATE_ID', '')
        
        # OTP storage (use Redis in production)
        self.otp_storage = {}
        
        # MSG91 configuration
        self.msg91_base_url = "https://control.msg91.com/api/v5"
        
        # Twilio configuration (alternative)
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER', '')
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number - remove spaces, dashes"""
        phone = ''.join(filter(str.isdigit, phone))
        
        # Ensure it starts with 91 for India
        if len(phone) == 10:
            phone = f"91{phone}"
        
        return phone
    
    def generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    def send_otp_msg91(self, phone: str, otp: str) -> Dict:
        """Send OTP via MSG91"""
        try:
            phone = self._format_phone(phone)
            
            url = f"{self.msg91_base_url}/otp"
            
            params = {
                "template_id": self.template_id,
                "mobile": phone,
                "authkey": self.api_key,
                "otp": otp
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "OTP sent successfully",
                    "provider": "MSG91"
                }
            else:
                return {
                    "success": False,
                    "error": f"MSG91 API error: {response.text}"
                }
                
        except Exception as e:
            print(f"MSG91 error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_otp_twilio(self, phone: str, otp: str) -> Dict:
        """Send OTP via Twilio"""
        try:
            from twilio.rest import Client
            
            phone = self._format_phone(phone)
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            message = client.messages.create(
                body=f"Your Pure & Desi verification code is: {otp}. Valid for 10 minutes.",
                from_=self.twilio_phone,
                to=f"+{phone}"
            )
            
            return {
                "success": True,
                "message": "OTP sent successfully",
                "provider": "Twilio",
                "sid": message.sid
            }
            
        except Exception as e:
            print(f"Twilio error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_otp(self, phone: str) -> Dict:
        """
        Send OTP to phone number
        
        Args:
            phone: Phone number
            
        Returns:
            Dict with send status
        """
        try:
            phone = self._format_phone(phone)
            otp = self.generate_otp()
            
            # Store OTP with expiry
            self.otp_storage[phone] = {
                "otp": otp,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=10),
                "attempts": 0
            }
            
            # Send based on provider
            if self.provider == 'MSG91' and self.api_key:
                result = self.send_otp_msg91(phone, otp)
            elif self.provider == 'TWILIO' and self.twilio_account_sid:
                result = self.send_otp_twilio(phone, otp)
            else:
                # Mock mode for development
                result = self._mock_send_otp(phone, otp)
            
            if result.get('success'):
                return {
                    "success": True,
                    "message": "OTP sent successfully",
                    "phone": phone,
                    "expires_in": 600  # 10 minutes
                }
            else:
                return result
                
        except Exception as e:
            print(f"Send OTP error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_otp(self, phone: str, otp: str) -> Dict:
        """
        Verify OTP
        
        Args:
            phone: Phone number
            otp: OTP to verify
            
        Returns:
            Dict with verification status
        """
        try:
            phone = self._format_phone(phone)
            
            if phone not in self.otp_storage:
                return {
                    "success": False,
                    "verified": False,
                    "error": "OTP not found. Please request a new one."
                }
            
            stored_data = self.otp_storage[phone]
            
            # Check if expired
            if datetime.now() > stored_data['expires_at']:
                del self.otp_storage[phone]
                return {
                    "success": False,
                    "verified": False,
                    "error": "OTP expired. Please request a new one."
                }
            
            # Check attempts
            if stored_data['attempts'] >= 3:
                del self.otp_storage[phone]
                return {
                    "success": False,
                    "verified": False,
                    "error": "Too many failed attempts. Please request a new OTP."
                }
            
            # Verify OTP
            if stored_data['otp'] == otp:
                del self.otp_storage[phone]
                return {
                    "success": True,
                    "verified": True,
                    "message": "OTP verified successfully",
                    "phone": phone
                }
            else:
                stored_data['attempts'] += 1
                return {
                    "success": False,
                    "verified": False,
                    "error": "Invalid OTP",
                    "attempts_remaining": 3 - stored_data['attempts']
                }
                
        except Exception as e:
            print(f"Verify OTP error: {str(e)}")
            return {
                "success": False,
                "verified": False,
                "error": str(e)
            }
    
    def send_order_sms(self, phone: str, order_id: str, amount: float) -> Dict:
        """Send order confirmation SMS"""
        try:
            phone = self._format_phone(phone)
            message = f"Your order {order_id} for Rs.{amount:.2f} has been confirmed. Track at pureanddesi.com/track - Pure & Desi"
            
            return self._send_sms(phone, message)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_shipping_sms(self, phone: str, order_id: str, tracking_number: str) -> Dict:
        """Send shipping notification SMS"""
        try:
            phone = self._format_phone(phone)
            message = f"Your order {order_id} has been shipped! Tracking: {tracking_number}. Track at pureanddesi.com/track - Pure & Desi"
            
            return self._send_sms(phone, message)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_sms(self, phone: str, message: str) -> Dict:
        """Internal method to send SMS"""
        try:
            if self.provider == 'MSG91' and self.api_key:
                url = f"{self.msg91_base_url}/flow"
                
                payload = {
                    "sender": self.sender_id,
                    "route": "4",
                    "country": "91",
                    "sms": [{
                        "message": message,
                        "to": [phone]
                    }]
                }
                
                headers = {
                    "authkey": self.api_key,
                    "content-type": "application/json"
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    return {"success": True, "message": "SMS sent"}
                else:
                    return {"success": False, "error": response.text}
            else:
                return self._mock_send_sms(phone, message)
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _mock_send_otp(self, phone: str, otp: str) -> Dict:
        """Mock OTP sending for development"""
        print(f"📱 [MOCK SMS] OTP to {phone}: {otp}")
        print(f"   Message: Your Pure & Desi verification code is: {otp}")
        
        return {
            "success": True,
            "message": "OTP sent (mock mode)",
            "provider": "MOCK",
            "mock": True
        }
    
    def _mock_send_sms(self, phone: str, message: str) -> Dict:
        """Mock SMS sending for development"""
        print(f"📱 [MOCK SMS] to {phone}")
        print(f"   Message: {message}")
        
        return {
            "success": True,
            "message": "SMS sent (mock mode)",
            "mock": True
        }
    
    def resend_otp(self, phone: str) -> Dict:
        """Resend OTP"""
        # Clear existing OTP
        phone = self._format_phone(phone)
        if phone in self.otp_storage:
            del self.otp_storage[phone]
        
        # Send new OTP
        return self.send_otp(phone)


# Create singleton instance
sms_service = SMSService()