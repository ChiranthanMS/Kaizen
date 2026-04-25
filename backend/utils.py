import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

def clean_decimal(value: Any) -> Decimal:
    """Safely convert value to Decimal, handling currency symbols and commas"""
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        # Remove currency symbols and commas
        clean_val = value.replace('₹', '').replace('$', '').replace(',', '').strip()
        if not clean_val:
            return Decimal('0')
        try:
            return Decimal(clean_val)
        except Exception:
            logger.warning(f"Could not convert '{value}' to Decimal, returning 0")
            return Decimal('0')
    return Decimal('0')
