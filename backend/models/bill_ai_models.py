from pydantic import BaseModel, Field, validator
from typing import Optional, Literal

Category = Literal["food", "rent", "travel"]
PaymentMethod = Literal["cash", "card", "upi", "netbanking", "other"]
Currency = Literal["INR", "USD", "EUR", "other"]

class GeminiBillSchema(BaseModel):
    category: Category
    bill_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    amount: Optional[float] = Field(None, description="Amount without currency symbol")
    vendor: Optional[str] = None
    travel_from: Optional[str] = None
    travel_to: Optional[str] = None
    description: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    invoice_number: Optional[str] = None
    tax_amount: Optional[float] = None
    total_amount_with_tax: Optional[float] = None
    currency: Optional[Currency] = None

    @validator("bill_date")
    def validate_date(cls, v):
        if v is None:
            return v
        # basic YYYY-MM-DD format check
        import re
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            raise ValueError("bill_date must be in YYYY-MM-DD format")
        return v

    class Config:
        extra = "ignore"