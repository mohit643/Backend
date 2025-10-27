# Backend/app/config/shipping_config.py

"""
========================================
SHIPPING CONFIGURATION - SINGLE SOURCE
========================================

🎯 Change FREE_SHIPPING_THRESHOLD here and it applies EVERYWHERE!

Want ₹800? Change to: 800
Want ₹1000? Change to: 1000
Want ₹1500? Change to: 1500
"""

class ShippingConfig:
    """Centralized shipping configuration for backend"""
    
    # 🎯 CHANGE THIS VALUE - IT APPLIES TO ENTIRE BACKEND
    FREE_SHIPPING_THRESHOLD = 999000000
    
    # Default values
    DEFAULT_SHIPPING_CHARGE = 50
    DEFAULT_COD_CHARGE = 40
    DEFAULT_WEIGHT_PER_ITEM = 1.0  # kg
    
    @classmethod
    def is_free_shipping_eligible(cls, subtotal: float) -> bool:
        """Check if order qualifies for free shipping"""
        return subtotal >= cls.FREE_SHIPPING_THRESHOLD
    
    @classmethod
    def get_shipping_charge(cls, subtotal: float, calculated_charge: float) -> float:
        """Get final shipping charge after applying free shipping logic"""
        if cls.is_free_shipping_eligible(subtotal):
            return 0.0
        return calculated_charge
    
    @classmethod
    def get_amount_needed_for_free_shipping(cls, subtotal: float) -> float:
        """Calculate amount needed to reach free shipping"""
        remaining = cls.FREE_SHIPPING_THRESHOLD - subtotal
        return remaining if remaining > 0 else 0
    
    @classmethod
    def get_threshold(cls) -> float:
        """Get the free shipping threshold value"""
        return cls.FREE_SHIPPING_THRESHOLD


# Create singleton instance
shipping_config = ShippingConfig()