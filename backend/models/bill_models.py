from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    LODGING = "lodging"
    FUEL = "fuel"
    ENTERTAINMENT = "entertainment"
    OFFICE_SUPPLIES = "office_supplies"
    COMMUNICATION = "communication"
    MEDICAL = "medical"
    MISCELLANEOUS = "miscellaneous"

class BillType(str, Enum):
    RENT = "rent"
    TRAVEL = "travel"
    FOOD = "food"

class BillProcessingRequest(BaseModel):
    filename: str
    file_type: str

class LineItem(BaseModel):
    name: str
    qty: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None

class ParsedLineItem(BaseModel):
    """Line item model matching the exact schema requirements"""
    description: str
    quantity: float
    unit_price: float
    total_price: float

class FinancialData(BaseModel):
    date: Optional[str] = Field(None, description="Date of the expense (YYYY-MM-DD)")
    vendor: Optional[str] = Field(None, description="Vendor or store name")
    category: Optional[str] = Field(None, description="Expense category")
    amount: Optional[float] = Field(None, description="Total amount")
    subtotal: Optional[float] = Field(None, description="Subtotal before tax")
    tax: Optional[float] = Field(None, description="Tax amount")
    discount: Optional[float] = Field(None, description="Discount amount")
    currency: Optional[str] = Field("USD", description="Currency code")
    remarks: Optional[str] = Field(None, description="Additional remarks or notes")
    line_items: Optional[List[LineItem]] = Field(default_factory=list, description="Parsed line items")

class ParsedFinancialData(BaseModel):
    """Financial data model matching the exact schema requirements"""
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    vendor: Optional[str] = Field(None, description="Vendor name")
    bill_type: Optional[BillType] = Field(None, description="Bill type: rent, travel, or food")
    currency: Optional[str] = Field(None, description="ISO currency code like USD, EUR, INR")
    subtotal: Optional[float] = Field(None, description="Subtotal amount")
    tax_rate_percent: Optional[float] = Field(None, description="Tax rate as percentage (e.g., 7.5 not 7.5%)")
    tax_amount: Optional[float] = Field(None, description="Tax amount")
    total_amount: Optional[float] = Field(None, description="Total amount")
    discount_amount: Optional[float] = Field(None, description="Discount amount")
    remarks: Optional[str] = Field(None, description="Additional remarks or notes")
    line_items: List[ParsedLineItem] = Field(default_factory=list, description="List of line items")

class BillProcessingResponse(BaseModel):
    success: bool
    filename: Optional[str] = None
    file_type: Optional[str] = None
    raw_text: Optional[str] = None
    financial_data: Optional[FinancialData] = None
    confidence_score: Optional[float] = Field(None, description="Confidence in extraction accuracy", ge=0, le=1)
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    error: Optional[str] = None
    warnings: Optional[List[str]] = Field(default_factory=list, description="Processing warnings")

class BillValidationResult(BaseModel):
    is_valid: bool
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    policy_compliance: Dict[str, Any] = Field(default_factory=dict)

class BillAnalytics(BaseModel):
    total_bills_processed: int
    success_rate: float
    average_processing_time: float
    category_distribution: Dict[ExpenseCategory, int]
    monthly_totals: Dict[str, float]