# backend/app/utils/order_id_generator.py (NEW FILE - CREATE THIS)

from datetime import datetime
import random
import string

def generate_order_id() -> str:
    """
    Generate unique order ID in format: PD20251025HHMMSS
    PD = Pure & Desi
    YYYYMMDDHHMMSS = Timestamp
    """
    now = datetime.now()
    
    # Format: PD + YYYYMMDD + HHMMSS
    order_id = f"PD{now.strftime('%Y%m%d%H%M%S')}"
    
    return order_id


def generate_order_id_with_random() -> str:
    """
    Generate unique order ID with random suffix
    Format: PD20251025HHMMSS + 4 random chars
    """
    now = datetime.now()
    
    # Random 4 character suffix
    random_suffix = ''.join(random.choices(string.digits, k=4))
    
    # Format: PD + YYYYMMDD + HHMMSS + XXXX
    order_id = f"PD{now.strftime('%Y%m%d%H%M%S')}{random_suffix}"
    
    return order_id


def generate_waybill_number(order_id: str) -> str:
    """
    Generate waybill number from order ID
    Format: PDEL + order_id (without PD prefix)
    """
    # Remove 'PD' prefix and add 'PDEL'
    waybill = f"PDEL{order_id[2:]}"
    return waybill


# Example usage:
if __name__ == "__main__":
    # Test order ID generation
    order_id = generate_order_id()
    print(f"Order ID: {order_id}")
    
    # Test waybill generation
    waybill = generate_waybill_number(order_id)
    print(f"Waybill: {waybill}")