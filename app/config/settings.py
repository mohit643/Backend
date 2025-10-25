# backend/app/config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # App Configuration
    app_name: str = Field(default="Pure & Desi API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:Mohit%4018@localhost:5432/pure_and_desi",
        env="DATABASE_URL"
    )
    
    # CORS - Will be parsed from JSON string
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],
        env="CORS_ORIGINS"
    )
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from JSON string or list"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback to comma-separated
                return [x.strip() for x in v.split(',')]
        return v
    
    # Google OAuth
    google_client_id: str = Field(
        default="915462319895-dsml59ip8t1jc92tjfv4mg6c94p6n086.apps.googleusercontent.com",
        env="GOOGLE_CLIENT_ID"
    )
    google_client_secret: str = Field(default="", env="GOOGLE_CLIENT_SECRET")
    
    # ========================================
    # SMS/OTP Configuration
    # ========================================
    development_mode: bool = Field(default=False, env="DEVELOPMENT_MODE")
    sms_provider: str = Field(default="msg91", env="SMS_PROVIDER")
    
    # MSG91 Configuration
    msg91_auth_key: str = Field(default="473918ADrf8JnYWUX68f0e387P1", env="MSG91_AUTH_KEY")
    msg91_sender_id: str = Field(default="PURDSI", env="MSG91_SENDER_ID")
    msg91_template_id: str = Field(default="68f0e555fbad781e0a293603", env="MSG91_TEMPLATE_ID")
    msg91_route: str = Field(default="4", env="MSG91_ROUTE")
    msg91_default_template_id: str = Field(default="68f0e555fbad781e0a293603", env="MSG91_DEFAULT_TEMPLATE_ID")
    
    # SMS Template IDs
    sms_otp_template_id: str = Field(default="68f0e555fbad781e0a293603", env="SMS_OTP_TEMPLATE_ID")
    sms_order_confirmation_template_id: str = Field(default="", env="SMS_ORDER_CONFIRMATION_TEMPLATE_ID")
    sms_shipping_update_template_id: str = Field(default="", env="SMS_SHIPPING_UPDATE_TEMPLATE_ID")
    sms_delivery_notification_template_id: str = Field(default="", env="SMS_DELIVERY_NOTIFICATION_TEMPLATE_ID")
    
    @field_validator('development_mode', mode='before')
    @classmethod
    def parse_development_mode(cls, v):
        """Parse development_mode from string to boolean"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    # Twilio (Alternative)
    twilio_account_sid: str = Field(default="", env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(default="", env="TWILIO_PHONE_NUMBER")
    
    # ========================================
    # Delhivery Shipping
    # ========================================
    delhivery_api_key: str = Field(default="", env="DELHIVERY_API_KEY")
    delhivery_use_staging: bool = Field(default=True, env="DELHIVERY_USE_STAGING")
    
    # ========================================
    # Razorpay Payment
    # ========================================
    razorpay_key_id: str = Field(default="rzp_test_RSpZwHYSfNHrBG", env="RAZORPAY_KEY_ID")
    razorpay_key_secret: str = Field(default="CBTjXkvUjzgeJux5DmT2dRvR", env="RAZORPAY_KEY_SECRET")
    
    # ========================================
    # WhatsApp Business API
    # ========================================
    whatsapp_api_token: str = Field(default="", env="WHATSAPP_API_TOKEN")
    whatsapp_phone_number_id: str = Field(default="", env="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_business_phone: str = Field(default="+919876543210", env="WHATSAPP_BUSINESS_PHONE")
    
    # ========================================
    # Email Configuration
    # ========================================
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    from_email: str = Field(default="noreply@pureanddesi.com", env="FROM_EMAIL")
    from_name: str = Field(default="Pure & Desi", env="FROM_NAME")
    admin_email: str = Field(default="admin@pureanddesi.com", env="ADMIN_EMAIL")
    
    # ========================================
    # Warehouse/Business Details
    # ========================================
    warehouse_name: str = Field(default="Pure & Desi Warehouse", env="WAREHOUSE_NAME")
    warehouse_address: str = Field(default="Green Street, Organic Market, New Delhi", env="WAREHOUSE_ADDRESS")
    warehouse_city: str = Field(default="Delhi", env="WAREHOUSE_CITY")
    warehouse_state: str = Field(default="Delhi", env="WAREHOUSE_STATE")
    warehouse_pincode: str = Field(default="110001", env="WAREHOUSE_PINCODE")
    warehouse_phone: str = Field(default="+919876543210", env="WAREHOUSE_PHONE")
    company_name: str = Field(default="Pure & Desi", env="COMPANY_NAME")
    gst_number: str = Field(default="", env="GST_NUMBER")
    
    # ========================================
    # JWT Configuration
    # ========================================
    jwt_secret_key: str = Field(default="your_super_secret_jwt_key_change_this", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # ========================================
    # Frontend URL
    # ========================================
    frontend_url: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    
    # ========================================
    # File Upload
    # ========================================
    max_upload_size: int = Field(default=5242880, env="MAX_UPLOAD_SIZE")  # 5MB
    allowed_extensions: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "pdf"],
        env="ALLOWED_EXTENSIONS"
    )
    
    @field_validator('allowed_extensions', mode='before')
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Parse allowed extensions from JSON string or list"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [x.strip() for x in v.split(',')]
        return v
    
    # ========================================
    # Rate Limiting
    # ========================================
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # ========================================
    # Logging
    # ========================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # ========================================
    # Computed Properties
    # ========================================
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return not self.debug
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.debug
    
    @property
    def msg91_base_url(self) -> str:
        """MSG91 API base URL"""
        return "https://control.msg91.com/api/v5"
    
    @property
    def delhivery_base_url(self) -> str:
        """Delhivery API base URL"""
        if self.delhivery_use_staging:
            return "https://staging-express.delhivery.com/api"
        return "https://track.delhivery.com/api"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


# Create singleton settings instance
settings = Settings()


# ==========================================
# Validation and Startup Functions
# ==========================================

def validate_settings():
    """Validate settings and print configuration status"""
    print("\n" + "="*70)
    print("🚀 PURE & DESI API - CONFIGURATION STATUS")
    print("="*70)
    
    # App Info
    print(f"\n📱 Application")
    print(f"   Name: {settings.app_name}")
    print(f"   Version: {settings.app_version}")
    print(f"   Environment: {'🔧 Development' if settings.is_development else '🏭 Production'}")
    print(f"   Debug Mode: {'✅ Enabled' if settings.debug else '❌ Disabled'}")
    
    # Database
    print(f"\n🗄️  Database")
    if "postgresql" in settings.database_url.lower():
        print(f"   Status: ✅ PostgreSQL Connected")
    else:
        print(f"   Status: ⚠️  Using SQLite (not recommended for production)")
    
    # Google OAuth
    print(f"\n🔐 Google OAuth")
    if settings.google_client_id and len(settings.google_client_id) > 20:
        print(f"   Status: ✅ Configured")
        print(f"   Client ID: {settings.google_client_id[:30]}...")
    else:
        print(f"   Status: ❌ Not configured")
    
    # SMS Service
    print(f"\n📱 SMS Service")
    print(f"   Provider: {settings.sms_provider.upper()}")
    print(f"   Development Mode: {'✅ Enabled (Mock)' if settings.development_mode else '❌ Disabled (Live)'}")
    if settings.msg91_auth_key and len(settings.msg91_auth_key) > 5:
        print(f"   MSG91: ✅ Configured")
        print(f"   Auth Key: {settings.msg91_auth_key[:10]}...")
        print(f"   Template ID: {settings.msg91_template_id}")
    else:
        print(f"   MSG91: ⚠️  Not configured (using mock)")
    
    # Email Service
    print(f"\n📧 Email Service")
    if settings.smtp_username and settings.smtp_password:
        print(f"   Status: ✅ Configured")
        print(f"   SMTP Host: {settings.smtp_host}:{settings.smtp_port}")
        print(f"   From: {settings.from_name} <{settings.from_email}>")
    else:
        print(f"   Status: ⚠️  Not configured (using mock)")
    
    # Payment Gateway
    print(f"\n💳 Razorpay Payment")
    if settings.razorpay_key_id and settings.razorpay_key_secret:
        mode = "TEST" if "test" in settings.razorpay_key_id else "LIVE"
        print(f"   Status: ✅ Configured ({mode} mode)")
        print(f"   Key ID: {settings.razorpay_key_id}")
    else:
        print(f"   Status: ⚠️  Not configured (using mock)")
    
    # Shipping Service
    print(f"\n📦 Delhivery Shipping")
    if settings.delhivery_api_key and len(settings.delhivery_api_key) > 5:
        mode = "STAGING" if settings.delhivery_use_staging else "PRODUCTION"
        print(f"   Status: ✅ Configured ({mode})")
    else:
        print(f"   Status: ⚠️  Not configured (using mock)")
    
    # WhatsApp
    print(f"\n💬 WhatsApp Business")
    if settings.whatsapp_api_token and settings.whatsapp_phone_number_id:
        print(f"   Status: ✅ Configured")
    else:
        print(f"   Status: ⚠️  Not configured (using mock)")
    
    # Warehouse Info
    print(f"\n🏢 Warehouse Details")
    print(f"   Name: {settings.warehouse_name}")
    print(f"   Location: {settings.warehouse_city}, {settings.warehouse_state}")
    print(f"   Pincode: {settings.warehouse_pincode}")
    
    # CORS
    print(f"\n🌐 CORS Origins")
    for origin in settings.cors_origins:
        print(f"   - {origin}")
    
    # Warnings
    warnings = []
    
    if settings.jwt_secret_key == "your_super_secret_jwt_key_change_this":
        warnings.append("⚠️  JWT_SECRET_KEY should be changed in production!")
    
    if settings.is_production and not settings.smtp_username:
        warnings.append("⚠️  Email not configured - notifications won't be sent!")
    
    if settings.is_production and settings.development_mode:
        warnings.append("⚠️  SMS Development Mode is ON in production!")
    
    if warnings:
        print(f"\n⚠️  WARNINGS")
        for warning in warnings:
            print(f"   {warning}")
    
    print("\n" + "="*70)
    print("✅ Configuration loaded successfully!")
    print("="*70 + "\n")


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is properly configured and enabled"""
    features = {
        'email': bool(settings.smtp_username and settings.smtp_password),
        'sms': bool(settings.msg91_auth_key and not settings.development_mode),
        'sms_mock': settings.development_mode,
        'whatsapp': bool(settings.whatsapp_api_token and settings.whatsapp_phone_number_id),
        'payment': bool(settings.razorpay_key_id and settings.razorpay_key_secret),
        'shipping': bool(settings.delhivery_api_key),
        'oauth': bool(settings.google_client_id and len(settings.google_client_id) > 20),
    }
    return features.get(feature, False)


def get_upload_config() -> dict:
    """Get file upload configuration"""
    return {
        'max_size': settings.max_upload_size,
        'max_size_mb': settings.max_upload_size / (1024 * 1024),
        'allowed_extensions': settings.allowed_extensions
    }


# Export
__all__ = [
    'settings',
    'validate_settings',
    'is_feature_enabled',
    'get_upload_config'
]