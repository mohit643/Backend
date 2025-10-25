# backend/app/services/google_oauth_service.py
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleOAuthService:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not self.client_id:
            print("⚠️ WARNING: GOOGLE_CLIENT_ID not found in environment variables")
        else:
            print(f"✅ Google Client ID loaded: {self.client_id[:20]}...")
        
    def verify_google_token(self, token: str):
        """Verify Google ID token and extract user info"""
        try:
            if not self.client_id:
                return {
                    "success": False,
                    "error": "Google Client ID not configured"
                }
            
            print(f"🔍 Verifying token with Client ID: {self.client_id[:20]}...")
            
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.client_id
            )
            
            print(f"✅ Token verified successfully")
            print(f"📧 Email: {idinfo.get('email')}")
            print(f"👤 Name: {idinfo.get('name')}")
            
            # Check if token is for our app
            if idinfo['aud'] != self.client_id:
                return {
                    "success": False,
                    "error": "Token audience mismatch"
                }
            
            # Extract user information
            return {
                "success": True,
                "email": idinfo.get('email'),
                "name": idinfo.get('name'),
                "picture": idinfo.get('picture'),
                "google_id": idinfo.get('sub'),
                "email_verified": idinfo.get('email_verified', False),
                "given_name": idinfo.get('given_name'),
                "family_name": idinfo.get('family_name')
            }
            
        except ValueError as e:
            # Invalid token
            error_msg = str(e)
            print(f"❌ Token verification failed: {error_msg}")
            return {
                "success": False,
                "error": f"Invalid token: {error_msg}"
            }
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Verification failed: {str(e)}"
            }

# Create singleton instance
google_oauth_service = GoogleOAuthService()