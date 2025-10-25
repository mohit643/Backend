# backend/app/utils/__init__.py (NEW FILE - CREATE THIS)

from .order_id_generator import (
    generate_order_id,
    generate_order_id_with_random,
    generate_waybill_number
)

__all__ = [
    "generate_order_id",
    "generate_order_id_with_random",
    "generate_waybill_number"
]
