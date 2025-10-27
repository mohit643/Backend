# backend/test_shiprocket_detailed.py
from app.config.settings import settings
from app.services.shiprocket_service import shiprocket_service
import json

print("\n" + "="*60)
print("🔍 DETAILED SHIPROCKET TEST")
print("="*60)

# 1. Configuration Check
print("\n1️⃣ Configuration:")
print(f"   Debug: {settings.debug}")
print(f"   Email: {settings.shiprocket_email}")
print(f"   Password: {'✓' if settings.shiprocket_password else '✗'}")
print(f"   Warehouse: {settings.warehouse_pincode}")

# 2. Login Test
print("\n2️⃣ Login Test:")
try:
    token = shiprocket_service.token
    if token:
        print(f"   ✅ Login successful")
        print(f"   Token: {token[:50]}...")
    else:
        print(f"   ❌ Login failed")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# 3. Pincode Test
print("\n3️⃣ Pincode Serviceability:")
test_pincodes = ["212601", "110001", "400001", "560001"]
for pincode in test_pincodes:
    try:
        result = shiprocket_service.check_pincode_serviceability(pincode)
        print(f"   {pincode}: {'✅ Serviceable' if result.get('serviceable') else '❌ Not Serviceable'}")
    except Exception as e:
        print(f"   {pincode}: ❌ Error - {str(e)}")

# 4. Shipping Rate Test
print("\n4️⃣ Shipping Rate Calculation:")
try:
    rate = shiprocket_service.calculate_shipping_charges("212601", 1.0, 0)
    print(f"   ✅ Rate calculated: ₹{rate.get('total_charge', 'N/A')}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

print("\n" + "="*60)
print("✅ Test Complete!")
print("="*60 + "\n")