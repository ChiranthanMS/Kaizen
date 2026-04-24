from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime, date
from enum import Enum

class BillStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"

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

class BillCreate(BaseModel):
    filename: Optional[str] = None
    file_type: Optional[str] = None
    date: Optional[date] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    discount: Optional[float] = None
    currency: str = "USD"
    remarks: Optional[str] = None
    raw_text: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    status: BillStatus = BillStatus.PENDING

class BillResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    department: Optional[str] = None
    filename: Optional[str] = None
    file_type: Optional[str] = None
    # Store as Python date; validator will coerce from str/datetime
    date: Optional[date] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    discount: Optional[float] = None
    currency: str = "USD"
    remarks: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    status: str = "pending"
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator("date", mode="before")
    @classmethod
    def _coerce_date(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            # Try ISO format first
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except Exception:
                # Fallback: try common dd/mm/yyyy or mm/dd/yyyy
                for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
                    try:
                        return datetime.strptime(v, fmt).date()
                    except Exception:
                        continue
        # If parsing failed, return None rather than raising
        return None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }

class BillUpdate(BaseModel):
    status: Optional[BillStatus] = None
    remarks: Optional[str] = None

class BillListResponse(BaseModel):
    bills: List[BillResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class BillStatistics(BaseModel):
    total_bills: int = 0
    total_amount: float = 0.0
    avg_amount: float = 0.0
    approved_bills: int = 0
    pending_bills: int = 0
    rejected_bills: int = 0
    
class EmployeeBillSummary(BaseModel):
    employee_id: int
    employee_name: str
    employee_email: str
    department: Optional[str] = None
    total_bills: int = 0
    total_amount: float = 0.0
    pending_bills: int = 0
    approved_bills: int = 0
    rejected_bills: int = 0
    last_submission: Optional[datetime] = None

class BillProcessingResult(BaseModel):
    success: bool
    bill_id: Optional[int] = None
    message: str
    bill_data: Optional[BillResponse] = None
    error: Optional[str] = None