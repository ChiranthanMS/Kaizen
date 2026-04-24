from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal
from datetime import datetime, date

class EmployeeDesignation(str, Enum):
    """Employee designation hierarchy"""
    INTERN = "intern"
    ASSOCIATE = "associate"
    SENIOR_ASSOCIATE = "senior_associate"
    MANAGER = "manager"
    SENIOR_MANAGER = "senior_manager"
    DIRECTOR = "director"
    SENIOR_DIRECTOR = "senior_director"
    VP = "vp"
    SVP = "svp"

class CityTier(str, Enum):
    """City tier classification for budget allocation"""
    TIER_1 = "tier_1"  # Mumbai, Delhi, Bangalore, Chennai, Hyderabad, Pune
    TIER_2 = "tier_2"  # Ahmedabad, Kolkata, Surat, Jaipur, Lucknow, Kanpur
    TIER_3 = "tier_3"  # Smaller cities and towns

class ExpenseType(str, Enum):
    """Types of expenses for budget allocation"""
    TRAVEL = "travel"
    HOTEL = "hotel"
    FOOD = "food"
    LOCAL_TRANSPORT = "local_transport"
    MISCELLANEOUS = "miscellaneous"

class TripStatus(str, Enum):
    """Status of official company trip"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TripSubmissionStatus(str, Enum):
    """Status of trip submission for manager approval"""
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"

class OfficialTrip(BaseModel):
    """Official company trip with budget allocation"""
    trip_id: str = Field(..., description="Unique trip identifier")
    employee_id: str = Field(..., description="Employee ID")
    employee_name: str = Field(..., description="Employee name")
    designation: EmployeeDesignation = Field(..., description="Employee designation")
    
    # Trip details
    trip_purpose: str = Field(..., description="Purpose of the trip")
    destination_city: str = Field(..., description="Destination city")
    destination_tier: CityTier = Field(..., description="Destination city tier")
    
    # Trip dates
    start_date: date = Field(..., description="Trip start date")
    end_date: date = Field(..., description="Trip end date")
    duration_days: int = Field(..., description="Trip duration in days")
    
    # Budget allocation
    allocated_budget: Dict[str, Decimal] = Field(..., description="Allocated budget by expense type")
    total_allocated: Decimal = Field(..., description="Total allocated budget")
    
    # Trip status
    status: TripStatus = Field(default=TripStatus.PENDING, description="Trip status")
    approved_by: Optional[str] = Field(None, description="Manager who approved the trip")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    rejected_by: Optional[str] = Field(None, description="Manager who rejected the trip")
    rejected_at: Optional[datetime] = Field(None, description="Rejection timestamp")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    
    # Expense tracking
    expenses_submitted: Decimal = Field(default=Decimal('0'), description="Total expenses submitted")
    expenses_approved: Decimal = Field(default=Decimal('0'), description="Total expenses approved")
    remaining_budget: Decimal = Field(..., description="Remaining budget")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BudgetCap(BaseModel):
    """Budget cap for specific designation, city tier, and expense type"""
    designation: EmployeeDesignation
    city_tier: CityTier
    expense_type: ExpenseType
    daily_limit: Decimal = Field(..., description="Daily expense limit in INR")
    per_trip_multiplier: Decimal = Field(default=Decimal('1.0'), description="Multiplier for trip duration")
    currency: str = Field(default="INR", description="Currency code")

class EmployeeBudgetProfile(BaseModel):
    """Employee's budget profile with all applicable caps"""
    employee_id: str
    designation: EmployeeDesignation
    work_city: str
    city_tier: CityTier
    travel_budget: Dict[str, Decimal] = Field(default_factory=dict)
    hotel_budget: Dict[str, Decimal] = Field(default_factory=dict)
    food_budget: Dict[str, Decimal] = Field(default_factory=dict)
    local_transport_budget: Dict[str, Decimal] = Field(default_factory=dict)
    miscellaneous_budget: Dict[str, Decimal] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class TripBudgetValidationResult(BaseModel):
    """Result of budget validation for a trip expense"""
    is_within_budget: bool
    expense_type: ExpenseType
    amount: Decimal
    trip_id: str
    allocated_budget: Decimal
    used_budget: Decimal = Field(default=Decimal('0'))
    remaining_budget: Decimal
    warning_message: Optional[str] = None
    recommendation: Optional[str] = None

class CityMapping(BaseModel):
    """Mapping of cities to their tiers"""
    city_name: str
    city_tier: CityTier
    state: Optional[str] = None
    region: Optional[str] = None

class EmployeeProfileUpdate(BaseModel):
    """Model for updating employee profile with budget-related information"""
    designation: Optional[EmployeeDesignation] = None
    work_city: Optional[str] = None
    travel_city: Optional[str] = None  # For travel expenses
    department: Optional[str] = None
    manager_id: Optional[str] = None

class TripRequest(BaseModel):
    """Request model for creating a new official trip"""
    trip_purpose: str = Field(..., description="Purpose of the trip")
    destination_city: str = Field(..., description="Destination city")
    start_date: date = Field(..., description="Trip start date")
    end_date: date = Field(..., description="Trip end date")
    estimated_expenses: Optional[Dict[str, Decimal]] = Field(None, description="Estimated expenses by type")
    
class TripApproval(BaseModel):
    """Model for trip approval by manager"""
    trip_id: str = Field(..., description="Trip ID to approve")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    budget_adjustments: Optional[Dict[str, float]] = Field(None, description="Budget adjustments if any")

class ActiveTripSession(BaseModel):
    """Active trip session for expense validation"""
    trip_id: str
    employee_id: str
    designation: EmployeeDesignation
    destination_tier: CityTier
    allocated_budgets: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Allocated budget by expense type"
    )
    used_budgets: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Used budget by expense type"
    )
    remaining_budgets: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Remaining budget by expense type"
    )
    trip_start: date
    trip_end: date
    is_active: bool = Field(default=True)
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat()
        }

class TripSubmission(BaseModel):
    """Trip submission for manager approval with all bills"""
    id: Optional[int] = Field(None, description="Submission ID")
    trip_id: str = Field(..., description="Trip ID")
    employee_id: int = Field(..., description="Employee ID")
    employee_name: str = Field(..., description="Employee name")
    trip_purpose: str = Field(..., description="Trip purpose")
    destination_city: str = Field(..., description="Destination city")
    start_date: date = Field(..., description="Trip start date")
    end_date: date = Field(..., description="Trip end date")
    duration_days: int = Field(..., description="Trip duration in days")
    total_bills: int = Field(..., description="Total number of bills")
    total_amount: Decimal = Field(..., description="Total amount of all bills")
    allocated_budget: Decimal = Field(..., description="Total allocated budget")
    budget_utilization: Decimal = Field(..., description="Budget utilization percentage")
    submission_status: TripSubmissionStatus = Field(default=TripSubmissionStatus.SUBMITTED)
    manager_id: Optional[int] = Field(None, description="Manager ID")
    reviewed_by: Optional[int] = Field(None, description="Reviewer ID")
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    approval_comments: Optional[str] = Field(None, description="Approval comments")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TripSubmissionRequest(BaseModel):
    """Request to submit a completed trip for approval"""
    trip_id: str = Field(..., description="Trip ID to submit")
    submission_notes: Optional[str] = Field(None, description="Additional notes for manager")

class TripApprovalRequest(BaseModel):
    """Request to approve or reject a trip submission"""
    submission_id: int = Field(..., description="Submission ID")
    action: str = Field(..., description="Action: 'approve' or 'reject'")
    comments: Optional[str] = Field(None, description="Approval/rejection comments")
    reason: Optional[str] = Field(None, description="Rejection reason (required for reject)")

class TripSubmissionResponse(BaseModel):
    """Response for trip submission operations"""
    success: bool
    message: str
    submission_id: Optional[int] = None
    trip_id: Optional[str] = None
    bills_affected: Optional[int] = None