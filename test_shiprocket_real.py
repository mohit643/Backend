# backend/test_shiprocket_real.py
from app.config.settings import settings
from app.services.shiprocket_service import shiprocket_service

print("\n" + "="*60)
print("🔍 SHIPROCKET CONFIGURATION CHECK")
print("="*60)
print(f"Debug Mode: {settings.debug}")
print(f"Email: {settings.shiprocket_email}")
print(f"Password: {'*' * len(settings.shiprocket_password)}")
print(f"Warehouse Pincode: {settings.warehouse_pincode}")
print("="*60 + "\n")

# Test pincode check
print("Testing Pincode: 212601")
result = shiprocket_service.check_pincode_serviceability("212601")
print(f"\n✅ Result: {result}")

print("\nTesting Pincode: 110001")
result2 = shiprocket_service.check_pincode_serviceability("110001")
print(f"\n✅ Result: {result2}")    