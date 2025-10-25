from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

router = APIRouter()

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    phone: str
    subject: str
    message: str

class NewsletterSubscribe(BaseModel):
    email: EmailStr

# Store contact submissions (In production, use database)
CONTACT_SUBMISSIONS = []
NEWSLETTER_SUBSCRIBERS = []

@router.post("/submit")
async def submit_contact_form(form: ContactForm):
    """Submit contact form"""
    try:
        submission = {
            "id": len(CONTACT_SUBMISSIONS) + 1,
            "name": form.name,
            "email": form.email,
            "phone": form.phone,
            "subject": form.subject,
            "message": form.message,
            "status": "pending",
            "submitted_at": datetime.now().isoformat()
        }
        
        CONTACT_SUBMISSIONS.append(submission)
        
        # In production, send email notification to admin
        # and confirmation email to user
        
        return {
            "success": True,
            "message": "Your message has been received. We'll get back to you soon!",
            "ticket_id": submission["id"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/newsletter/subscribe")
async def subscribe_newsletter(data: NewsletterSubscribe):
    """Subscribe to newsletter"""
    try:
        # Check if already subscribed
        if data.email in NEWSLETTER_SUBSCRIBERS:
            return {
                "success": True,
                "message": "You are already subscribed to our newsletter!",
                "already_subscribed": True
            }
        
        NEWSLETTER_SUBSCRIBERS.append(data.email)
        
        # In production, send welcome email and add to email marketing service
        
        return {
            "success": True,
            "message": "Thank you for subscribing! Check your inbox for confirmation.",
            "email": data.email
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/submissions")
async def get_all_submissions():
    """Get all contact form submissions (Admin only)"""
    try:
        return {
            "total": len(CONTACT_SUBMISSIONS),
            "submissions": CONTACT_SUBMISSIONS
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info")
async def get_contact_info():
    """Get company contact information"""
    return {
        "company_name": "Pure & Desi",
        "email": "info@pureanddesi.com",
        "phone": "+91 9876543210",
        "whatsapp": "+91 9876543210",
        "address": "Green Street, Organic Market, New Delhi - 110001",
        "business_hours": "Monday - Saturday: 9:00 AM - 6:00 PM",
        "social_media": {
            "facebook": "https://facebook.com/pureanddesi",
            "instagram": "https://instagram.com/pureanddesi",
            "twitter": "https://twitter.com/pureanddesi"
        }
    }