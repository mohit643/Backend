import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
from app.config.settings import settings

class EmailService:
    """Email Service for sending notifications"""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host or "smtp.gmail.com"
        self.smtp_port = settings.smtp_port or 587
        self.smtp_username = settings.smtp_username or ""
        self.smtp_password = settings.smtp_password or ""
        self.from_email = settings.from_email or "noreply@pureanddesi.com"
        self.from_name = settings.from_name or "Pure & Desi"
    
    def _create_connection(self):
        """Create SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            return server
        except Exception as e:
            print(f"SMTP connection error: {str(e)}")
            return None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict:
        """
        Send email
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text body (optional)
            
        Returns:
            Dict with send status
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text part
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            server = self._create_connection()
            
            if server:
                server.send_message(msg)
                server.quit()
                
                return {
                    "success": True,
                    "message": "Email sent successfully",
                    "to": to_email
                }
            else:
                return self._mock_send(to_email, subject)
                
        except Exception as e:
            print(f"Email send error: {str(e)}")
            return self._mock_send(to_email, subject)
    
    def send_order_confirmation_email(
        self,
        to_email: str,
        customer_name: str,
        order_id: str,
        order_items: List[Dict],
        subtotal: float,
        shipping_cost: float,
        total: float,
        shipping_address: Dict
    ) -> Dict:
        """Send order confirmation email"""
        
        # Create items HTML
        items_html = ""
        for item in order_items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">
                    {item['productName']}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">
                    {item['quantity']}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">
                    ₹{item['price']:.2f}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">
                    ₹{(item['price'] * item['quantity']):.2f}
                </td>
            </tr>
            """
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">🌾 Pure & Desi</h1>
                <p style="margin: 10px 0 0 0;">Order Confirmation</p>
            </div>
            
            <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #16a34a; margin-top: 0;">Thank You, {customer_name}!</h2>
                <p>Your order has been confirmed and will be processed shortly.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
                    <h3 style="margin-top: 0; color: #16a34a;">Order Details</h3>
                    <p><strong>Order ID:</strong> {order_id}</p>
                    <p><strong>Order Date:</strong> {datetime.now().strftime("%d %B, %Y")}</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: white; border-radius: 8px; overflow: hidden;">
                    <thead>
                        <tr style="background: #16a34a; color: white;">
                            <th style="padding: 12px; text-align: left;">Product</th>
                            <th style="padding: 12px; text-align: center;">Qty</th>
                            <th style="padding: 12px; text-align: right;">Price</th>
                            <th style="padding: 12px; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <table style="width: 100%;">
                        <tr>
                            <td style="padding: 8px;">Subtotal:</td>
                            <td style="padding: 8px; text-align: right;">₹{subtotal:.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;">Shipping:</td>
                            <td style="padding: 8px; text-align: right;">₹{shipping_cost:.2f}</td>
                        </tr>
                        <tr style="border-top: 2px solid #eee; font-size: 18px; font-weight: bold; color: #16a34a;">
                            <td style="padding: 12px 8px;">Total:</td>
                            <td style="padding: 12px 8px; text-align: right;">₹{total:.2f}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #16a34a;">Shipping Address</h3>
                    <p style="margin: 5px 0;"><strong>{shipping_address['fullName']}</strong></p>
                    <p style="margin: 5px 0;">{shipping_address['address']}</p>
                    <p style="margin: 5px 0;">{shipping_address['city']}, {shipping_address['state']} - {shipping_address['pincode']}</p>
                    <p style="margin: 5px 0;">Phone: {shipping_address['phone']}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://thepureanddesi.com/orders/{order_id}" 
                       style="display: inline-block; background: #16a34a; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Track Your Order
                    </a>
                </div>
                
                <p style="text-align: center; color: #666; font-size: 14px; margin-top: 30px;">
                    Need help? Contact us at <a href="mailto:support@pureanddesi.com" style="color: #16a34a;">support@pureanddesi.com</a>
                </p>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
                <p>© 2025 Pure & Desi. All rights reserved.</p>
                <p>Traditional Cold-Pressed Oils</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=to_email,
            subject=f"Order Confirmed - {order_id} | Pure & Desi",
            html_body=html_body
        )
    
    def send_shipping_notification_email(
        self,
        to_email: str,
        customer_name: str,
        order_id: str,
        waybill: str,
        tracking_url: str,
        estimated_delivery: str
    ) -> Dict:
        """Send shipping notification email"""
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">📦 Your Order is Shipped!</h1>
            </div>
            
            <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #16a34a;">Hi {customer_name},</h2>
                <p>Great news! Your order has been shipped and is on its way to you.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
                    <p><strong>Order ID:</strong> {order_id}</p>
                    <p><strong>Tracking Number:</strong> {waybill}</p>
                    <p><strong>Estimated Delivery:</strong> {estimated_delivery}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{tracking_url}" 
                       style="display: inline-block; background: #16a34a; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Track Shipment
                    </a>
                </div>
                
                <p style="text-align: center; color: #666; margin-top: 30px;">
                    We'll notify you once your order is delivered!
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=to_email,
            subject=f"Your Order is Shipped - {order_id} | Pure & Desi",
            html_body=html_body
        )
    
    def send_contact_form_notification(
        self,
        admin_email: str,
        name: str,
        email: str,
        phone: str,
        subject: str,
        message: str
    ) -> Dict:
        """Send contact form notification to admin"""
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #16a34a;">New Contact Form Submission</h2>
            
            <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Phone:</strong> {phone}</p>
                <p><strong>Subject:</strong> {subject}</p>
                <p><strong>Message:</strong></p>
                <p style="background: white; padding: 15px; border-radius: 5px;">{message}</p>
            </div>
            
            <p><strong>Submitted:</strong> {datetime.now().strftime("%d %B, %Y at %I:%M %p")}</p>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=admin_email,
            subject=f"New Contact Form: {subject}",
            html_body=html_body
        )
    
    def _mock_send(self, to_email: str, subject: str) -> Dict:
        """Mock email sending for testing"""
        print(f"📧 [MOCK] Email to {to_email}: {subject}")
        
        return {
            "success": True,
            "message": "Email sent successfully (mock)",
            "to": to_email,
            "mock": True
        }


# Create singleton instance
email_service = EmailService()