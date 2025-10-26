# backend/app/routers/auth.py (WITHOUT OTP - Only Google OAuth)
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.connection import get_db
from app.models.customer import Customer

router = APIRouter()

# ==================== REQUEST MODELS ====================
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
def format_phone(phone: str) -> str:
    """Format phone number"""
    phone = ''.join(filter(str.isdigit, phone))
    if not phone.startswith('91') and len(phone) == 10:
        phone = f"91{phone}"
    return phone

# ==================== ADMIN CHECK ENDPOINT ====================
@router.get("/check-admin")
async def check_admin(
    email: str = None,
    phone: str = None,
    db: Session = Depends(get_db)
):
    """Check if user is admin"""
    try:
        customer = None
        
        if email:
            customer = db.query(Customer).filter(Customer.email == email).first()
        elif phone:
            phone = format_phone(phone)
            customer = db.query(Customer).filter(Customer.phone == phone).first()
        
        if not customer:
            print(f"❌ Customer not found: {email or phone}")
            return {
                "success": False,
                "is_admin": False,
                "message": "Customer not found"
            }
        
        print(f"🔍 Admin check for: {customer.email or customer.phone}")
        print(f"✅ Is Admin: {customer.is_admin}")
        
        return {
            "success": True,
            "is_admin": bool(customer.is_admin),
            "email": customer.email,
            "phone": customer.phone,
            "full_name": customer.full_name
        }
        
    except Exception as e:
        print(f"❌ Error in check_admin: {str(e)}")
        return {
            "success": False,
            "is_admin": False,
            "error": str(e)
        }

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