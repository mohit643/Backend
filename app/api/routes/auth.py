# backend/app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import string
import os

from app.database.connection import get_db
from app.models.customer import Customer, OTP
from app.services.sms_service import get_sms_service

router = APIRouter()

# ==================== REQUEST MODELS ====================
class SendOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str

class UpdateProfileRequest(BaseModel):
    full_name: str
    email: str = None
    address: str = None
    city: str = None
    state: str = None
    pincode: str = None

class GoogleLoginRequest(BaseModel):
    credential: str  # Google ID token

# ==================== HELPER FUNCTIONS ====================
def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def format_phone(phone: str) -> str:
    """Format phone number"""
    phone = ''.join(filter(str.isdigit, phone))
    if not phone.startswith('91') and len(phone) == 10:
        phone = f"91{phone}"
    return phone

# ==================== OTP-BASED AUTH ====================
@router.post("/send-otp")
async def send_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """Send OTP to phone number"""
    try:
        phone = format_phone(request.phone)
        
        # Validate phone
        if len(phone) != 12:  # 91 + 10 digits
            raise HTTPException(status_code=400, detail="Invalid phone number")
        
        # Generate OTP
        otp_code = generate_otp()
        
        # Save OTP to database
        otp_entry = OTP(
            phone=phone,
            otp=otp_code,
            purpose="login",
            expires_at=datetime.now() + timedelta(minutes=10)
        )
        db.add(otp_entry)
        db.commit()
        
        # 📱 SEND OTP VIA SMS SERVICE
        sms_service = get_sms_service()
        sms_result = sms_service.send_otp(phone, otp_code)
        
        # Check if development mode
        development_mode = os.getenv("DEVELOPMENT_MODE", "True") == "True"
        
        # Response
        response = {
            "success": True,
            "message": "OTP sent successfully",
            "phone": request.phone,
            "expires_in": 600
        }
        
        # Only include OTP in response during development mode
        if development_mode:
            response["otp"] = otp_code
            print(f"📱 [DEV] OTP for {phone}: {otp_code}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in send_otp: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP and login/signup customer"""
    try:
        phone = format_phone(request.phone)
        
        # Find valid OTP
        otp_entry = db.query(OTP).filter(
            OTP.phone == phone,
            OTP.otp == request.otp,
            OTP.is_used == False,
            OTP.expires_at > datetime.now()
        ).first()
        
        if not otp_entry:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        # Mark OTP as used
        otp_entry.is_used = True
        db.commit()
        
        # Find or create customer
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        
        if not customer:
            # New customer - signup
            customer = Customer(
                phone=phone,
                is_verified=True,
                last_login=datetime.now()
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            
            return {
                "success": True,
                "message": "Account created successfully",
                "is_new_user": True,
                "customer": {
                    "id": customer.id,
                    "phone": customer.phone,
                    "full_name": customer.full_name,
                    "email": customer.email,
                    "authType": "phone"
                }
            }
        else:
            # Existing customer - login
            customer.last_login = datetime.now()
            customer.is_verified = True
            db.commit()
            
            return {
                "success": True,
                "message": "Login successful",
                "is_new_user": False,
                "customer": {
                    "id": customer.id,
                    "phone": customer.phone,
                    "full_name": customer.full_name,
                    "email": customer.email,
                    "address": customer.address,
                    "city": customer.city,
                    "state": customer.state,
                    "pincode": customer.pincode,
                    "authType": "phone"
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in verify_otp: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GOOGLE OAUTH AUTH ====================
@router.post("/google-login")
async def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Login/Signup with Google OAuth"""
    try:
        from app.services.google_oauth_service import google_oauth_service
        
        # Verify Google token
        google_data = google_oauth_service.verify_google_token(request.credential)
        
        if not google_data.get("success"):
            raise HTTPException(
                status_code=401, 
                detail=google_data.get("error", "Invalid Google token")
            )
        
        email = google_data["email"]
        name = google_data["name"]
        picture = google_data.get("picture", "")
        google_id = google_data["google_id"]
        
        # Find existing customer by Google ID or email
        customer = db.query(Customer).filter(
            (Customer.google_id == google_id) | (Customer.email == email)
        ).first()
        
        if customer:
            # Existing customer - update Google info
            customer.google_id = google_id
            customer.google_email = email
            customer.google_picture = picture
            customer.last_login = datetime.now()
            customer.is_verified = True
            
            # Update name if not set
            if not customer.full_name:
                customer.full_name = name
            
            db.commit()
            db.refresh(customer)
            
            return {
                "success": True,
                "message": "Login successful",
                "is_new_user": False,
                "customer": {
                    "id": customer.id,
                    "phone": customer.phone,
                    "email": customer.email,
                    "full_name": customer.full_name,
                    "picture": customer.google_picture,
                    "address": customer.address,
                    "city": customer.city,
                    "state": customer.state,
                    "pincode": customer.pincode,
                    "authType": "google"
                }
            }
        else:
            # New customer - create account
            new_customer = Customer(
                email=email,
                google_id=google_id,
                google_email=email,
                google_picture=picture,
                full_name=name,
                is_verified=True,
                last_login=datetime.now()
            )
            
            db.add(new_customer)
            db.commit()
            db.refresh(new_customer)
            
            return {
                "success": True,
                "message": "Account created successfully",
                "is_new_user": True,
                "customer": {
                    "id": new_customer.id,
                    "phone": new_customer.phone,
                    "email": new_customer.email,
                    "full_name": new_customer.full_name,
                    "picture": new_customer.google_picture,
                    "authType": "google"
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in google_login: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

# ==================== PROFILE MANAGEMENT ====================
@router.post("/update-profile")
async def update_profile(
    request: UpdateProfileRequest, 
    phone: str = None,
    email: str = None,
    db: Session = Depends(get_db)
):
    """Update customer profile (works with both phone and email)"""
    try:
        # Find customer by phone or email
        if phone:
            phone = format_phone(phone)
            customer = db.query(Customer).filter(Customer.phone == phone).first()
        elif email:
            customer = db.query(Customer).filter(Customer.email == email).first()
        else:
            raise HTTPException(status_code=400, detail="Phone or email required")
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Update fields
        if request.full_name:
            customer.full_name = request.full_name
        if request.email:
            customer.email = request.email
        if request.address:
            customer.address = request.address
        if request.city:
            customer.city = request.city
        if request.state:
            customer.state = request.state
        if request.pincode:
            customer.pincode = request.pincode
        
        db.commit()
        db.refresh(customer)
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "customer": {
                "id": customer.id,
                "phone": customer.phone,
                "email": customer.email,
                "full_name": customer.full_name,
                "picture": customer.google_picture,
                "address": customer.address,
                "city": customer.city,
                "state": customer.state,
                "pincode": customer.pincode
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in update_profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{identifier}")
async def get_profile(identifier: str, db: Session = Depends(get_db)):
    """Get customer profile by phone or email"""
    try:
        # Try to find by phone first
        if identifier.isdigit():
            phone = format_phone(identifier)
            customer = db.query(Customer).filter(Customer.phone == phone).first()
        else:
            # Try by email
            customer = db.query(Customer).filter(Customer.email == identifier).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {
            "id": customer.id,
            "phone": customer.phone,
            "email": customer.email,
            "full_name": customer.full_name,
            "picture": customer.google_picture,
            "address": customer.address,
            "city": customer.city,
            "state": customer.state,
            "pincode": customer.pincode,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
            "authType": "google" if customer.google_id else "phone"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))