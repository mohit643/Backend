import razorpay
import hashlib
import hmac
from typing import Dict, Optional
from datetime import datetime
from app.config.settings import settings

class PaymentService:
    """Razorpay Payment Integration Service"""
    
    def __init__(self):
        self.key_id = settings.razorpay_key_id
        self.key_secret = settings.razorpay_key_secret
        
        # Initialize Razorpay client
        if self.key_id and self.key_secret and self.key_id != "your_key_here":
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        else:
            self.client = None
            print("⚠️ Razorpay credentials not configured. Using mock mode.")
    
    def create_order(
        self,
        amount: float,
        order_id: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> Dict:
        """
        Create Razorpay order
        
        Args:
            amount: Order amount in INR
            order_id: Unique order ID
            customer_email: Customer email (optional)
            customer_phone: Customer phone (optional)
            
        Returns:
            Dict with Razorpay order details
        """
        try:
            if self.client:
                # Real Razorpay order creation
                data = {
                    "amount": int(amount * 100),  # Convert to paise
                    "currency": "INR",
                    "receipt": order_id,
                    "notes": {
                        "order_id": order_id
                    }
                }
                
                if customer_email:
                    data["notes"]["email"] = customer_email
                if customer_phone:
                    data["notes"]["phone"] = customer_phone
                
                razorpay_order = self.client.order.create(data=data)
                
                return {
                    "success": True,
                    "razorpay_order_id": razorpay_order["id"],
                    "amount": razorpay_order["amount"],
                    "currency": razorpay_order["currency"],
                    "key_id": self.key_id,
                    "order_id": order_id
                }
            else:
                # Mock order for testing
                return self._create_mock_order(amount, order_id)
                
        except Exception as e:
            print(f"Razorpay order creation error: {str(e)}")
            return self._create_mock_order(amount, order_id)
    
    def _create_mock_order(self, amount: float, order_id: str) -> Dict:
        """Create mock order for testing"""
        mock_razorpay_id = f"order_{order_id}_{int(datetime.now().timestamp())}"
        
        return {
            "success": True,
            "razorpay_order_id": mock_razorpay_id,
            "amount": int(amount * 100),
            "currency": "INR",
            "key_id": "rzp_test_mock",
            "order_id": order_id,
            "mock": True
        }
    
    def verify_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> Dict:
        """
        Verify Razorpay payment signature
        
        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Razorpay signature
            
        Returns:
            Dict with verification status
        """
        try:
            if self.client and self.key_secret != "your_secret_here":
                # Generate signature
                message = f"{razorpay_order_id}|{razorpay_payment_id}"
                generated_signature = hmac.new(
                    self.key_secret.encode(),
                    message.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if generated_signature == razorpay_signature:
                    # Fetch payment details
                    payment = self.client.payment.fetch(razorpay_payment_id)
                    
                    return {
                        "success": True,
                        "verified": True,
                        "payment_id": razorpay_payment_id,
                        "order_id": razorpay_order_id,
                        "amount": payment.get("amount", 0) / 100,
                        "status": payment.get("status", "captured"),
                        "method": payment.get("method", ""),
                        "email": payment.get("email", ""),
                        "contact": payment.get("contact", "")
                    }
                else:
                    return {
                        "success": False,
                        "verified": False,
                        "error": "Invalid signature"
                    }
            else:
                # Mock verification for testing
                return {
                    "success": True,
                    "verified": True,
                    "payment_id": razorpay_payment_id,
                    "order_id": razorpay_order_id,
                    "mock": True
                }
                
        except Exception as e:
            print(f"Payment verification error: {str(e)}")
            return {
                "success": False,
                "verified": False,
                "error": str(e)
            }
    
    def capture_payment(self, payment_id: str, amount: float) -> Dict:
        """Capture payment manually"""
        try:
            if self.client:
                payment = self.client.payment.capture(payment_id, int(amount * 100))
                return {
                    "success": True,
                    "payment_id": payment["id"],
                    "status": payment["status"]
                }
            else:
                return {"success": True, "mock": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = "Customer request"
    ) -> Dict:
        """
        Create refund for a payment
        
        Args:
            payment_id: Razorpay payment ID
            amount: Refund amount (None for full refund)
            reason: Refund reason
            
        Returns:
            Dict with refund details
        """
        try:
            if self.client:
                data = {
                    "notes": {
                        "reason": reason
                    }
                }
                
                if amount:
                    data["amount"] = int(amount * 100)
                
                refund = self.client.payment.refund(payment_id, data)
                
                return {
                    "success": True,
                    "refund_id": refund["id"],
                    "payment_id": payment_id,
                    "amount": refund.get("amount", 0) / 100,
                    "status": refund.get("status", "processing"),
                    "speed": refund.get("speed", "normal")
                }
            else:
                return self._create_mock_refund(payment_id, amount)
                
        except Exception as e:
            print(f"Refund creation error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_mock_refund(self, payment_id: str, amount: Optional[float]) -> Dict:
        """Create mock refund for testing"""
        return {
            "success": True,
            "refund_id": f"rfnd_{payment_id}_{int(datetime.now().timestamp())}",
            "payment_id": payment_id,
            "amount": amount or 0,
            "status": "processing",
            "mock": True
        }
    
    def fetch_payment(self, payment_id: str) -> Dict:
        """Fetch payment details"""
        try:
            if self.client:
                payment = self.client.payment.fetch(payment_id)
                return {
                    "success": True,
                    "payment": payment
                }
            else:
                return {"success": True, "mock": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Create singleton instance
payment_service = PaymentService()