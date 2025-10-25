# backend/services/notification_service.py
from typing import Dict, Optional
from .email_service import email_service
from .sms_service import sms_service
from .whatsapp_service import whatsapp_service

class NotificationService:
    """Unified notification service for Email, SMS, and WhatsApp"""
    
    def __init__(self):
        self.email = email_service
        self.sms = sms_service
        self.whatsapp = whatsapp_service
    
    def send_order_confirmation(
        self,
        customer_data: Dict,
        order_data: Dict,
        channels: list = ['email', 'whatsapp']
    ) -> Dict:
        """
        Send order confirmation across multiple channels
        
        Args:
            customer_data: Customer information
            order_data: Order details
            channels: List of channels to use ['email', 'sms', 'whatsapp']
            
        Returns:
            Dict with results from each channel
        """
        results = {}
        
        # Email notification
        if 'email' in channels and customer_data.get('email'):
            try:
                email_result = self.email.send_order_confirmation_email(
                    to_email=customer_data['email'],
                    customer_name=customer_data['fullName'],
                    order_id=order_data['order_id'],
                    order_items=order_data['items'],
                    subtotal=order_data['subtotal'],
                    shipping_cost=order_data['shipping_cost'],
                    total=order_data['total'],
                    shipping_address=customer_data
                )
                results['email'] = email_result
            except Exception as e:
                results['email'] = {"success": False, "error": str(e)}
        
        # SMS notification
        if 'sms' in channels and customer_data.get('phone'):
            try:
                sms_result = self.sms.send_order_sms(
                    phone=customer_data['phone'],
                    order_id=order_data['order_id'],
                    amount=order_data['total']
                )
                results['sms'] = sms_result
            except Exception as e:
                results['sms'] = {"success": False, "error": str(e)}
        
        # WhatsApp notification
        if 'whatsapp' in channels and customer_data.get('phone'):
            try:
                wa_result = self.whatsapp.send_order_confirmation(
                    phone_number=customer_data['phone'],
                    order_id=order_data['order_id'],
                    customer_name=customer_data['fullName'],
                    total_amount=order_data['total'],
                    items_count=len(order_data['items'])
                )
                results['whatsapp'] = wa_result
            except Exception as e:
                results['whatsapp'] = {"success": False, "error": str(e)}
        
        return {
            "success": any(r.get('success') for r in results.values()),
            "results": results
        }
    
    def send_shipping_notification(
        self,
        customer_data: Dict,
        order_data: Dict,
        shipping_data: Dict,
        channels: list = ['email', 'whatsapp']
    ) -> Dict:
        """Send shipping notification"""
        results = {}
        
        # Email
        if 'email' in channels and customer_data.get('email'):
            try:
                email_result = self.email.send_shipping_notification_email(
                    to_email=customer_data['email'],
                    customer_name=customer_data['fullName'],
                    order_id=order_data['order_id'],
                    waybill=shipping_data['waybill'],
                    tracking_url=shipping_data['tracking_url'],
                    estimated_delivery=shipping_data['estimated_delivery']
                )
                results['email'] = email_result
            except Exception as e:
                results['email'] = {"success": False, "error": str(e)}
        
        # SMS
        if 'sms' in channels and customer_data.get('phone'):
            try:
                sms_result = self.sms.send_shipping_sms(
                    phone=customer_data['phone'],
                    order_id=order_data['order_id'],
                    tracking_number=shipping_data['waybill']
                )
                results['sms'] = sms_result
            except Exception as e:
                results['sms'] = {"success": False, "error": str(e)}
        
        # WhatsApp
        if 'whatsapp' in channels and customer_data.get('phone'):
            try:
                wa_result = self.whatsapp.send_shipping_update(
                    phone_number=customer_data['phone'],
                    order_id=order_data['order_id'],
                    waybill=shipping_data['waybill'],
                    courier_name="Delhivery",
                    estimated_delivery=shipping_data['estimated_delivery']
                )
                results['whatsapp'] = wa_result
            except Exception as e:
                results['whatsapp'] = {"success": False, "error": str(e)}
        
        return {
            "success": any(r.get('success') for r in results.values()),
            "results": results
        }
    
    def send_delivery_notification(
        self,
        customer_data: Dict,
        order_id: str,
        channels: list = ['email', 'whatsapp']
    ) -> Dict:
        """Send delivery notification"""
        results = {}
        
        # WhatsApp
        if 'whatsapp' in channels and customer_data.get('phone'):
            try:
                wa_result = self.whatsapp.send_delivery_notification(
                    phone_number=customer_data['phone'],
                    order_id=order_id,
                    customer_name=customer_data['fullName']
                )
                results['whatsapp'] = wa_result
            except Exception as e:
                results['whatsapp'] = {"success": False, "error": str(e)}
        
        return {
            "success": any(r.get('success') for r in results.values()),
            "results": results
        }
    
    def send_otp(
        self,
        phone: str,
        channel: str = 'whatsapp'
    ) -> Dict:
        """Send OTP via specified channel"""
        if channel == 'whatsapp':
            return self.whatsapp.send_otp(phone)
        elif channel == 'sms':
            return self.sms.send_otp(phone)
        else:
            return {"success": False, "error": "Invalid channel"}
    
    def verify_otp(
        self,
        phone: str,
        otp: str,
        channel: str = 'whatsapp'
    ) -> Dict:
        """Verify OTP"""
        if channel == 'whatsapp':
            return self.whatsapp.verify_otp(phone, otp)
        elif channel == 'sms':
            return self.sms.verify_otp(phone, otp)
        else:
            return {"success": False, "error": "Invalid channel"}


# Create singleton instance
notification_service = NotificationService()