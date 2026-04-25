from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from decimal import Decimal
import logging

from models.budget_models import (
    EmployeeBudgetProfile, FundCapsSession, BudgetValidationResult,
    EmployeeDesignation, CityTier, ExpenseType, EmployeeProfileUpdate
)
from models.user_models import TokenData
from services.budget_service import budget_service
from dependencies.auth_dependencies import get_current_user
from utils import clean_decimal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/budget", tags=["Budget Management"])

@router.get("/fund-caps", response_model=Dict)
async def get_employee_fund_caps(current_user: TokenData = Depends(get_current_user)):
    """Get current employee's fund caps from active session"""
    
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can access fund caps"
        )
    
    try:
        # Get active session
        session = budget_service.get_active_session(current_user.user_id)
        
        if not session:
            # Create new session if none exists
            designation_str = current_user.designation or "associate"
            work_city = current_user.work_city or "Mumbai"
            
            designation = budget_service.get_designation_from_string(designation_str)
            
            session = budget_service.create_fund_caps_session(
                employee_id=current_user.user_id,
                designation=designation,
                work_city=work_city
            )
        
        return {
            "success": True,
            "employee_id": current_user.user_id,
            "designation": session.designation.value,
            "work_city_tier": session.work_city_tier.value,
            "fund_caps": session.fund_caps,
            "session_expires_at": session.expires_at,
            "message": "Fund caps retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving fund caps for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve fund caps: {str(e)}"
        )

@router.post("/validate-expense", response_model=BudgetValidationResult)
async def validate_expense_against_budget(
    expense_type: str,
    amount: float,
    current_daily_usage: float = 0.0,
    current_monthly_usage: float = 0.0,
    current_user: TokenData = Depends(get_current_user)
):
    """Validate an expense against employee's budget caps"""
    
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can validate expenses"
        )
    
    try:
        # Get active session
        session = budget_service.get_active_session(current_user.user_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active budget session found. Please login again."
            )
        
        # Convert expense type string to enum
        try:
            expense_type_enum = ExpenseType(expense_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid expense type: {expense_type}. Valid types: {[e.value for e in ExpenseType]}"
            )
        
        # Validate expense
        validation_result = budget_service.validate_expense_against_budget(
            session=session,
            expense_type=expense_type_enum,
            amount=clean_decimal(amount),
            current_daily_usage=clean_decimal(current_daily_usage),
            current_monthly_usage=clean_decimal(current_monthly_usage)
        )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating expense for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not validate expense: {str(e)}"
        )

@router.get("/profile", response_model=Dict)
async def get_employee_budget_profile(current_user: TokenData = Depends(get_current_user)):
    """Get employee's complete budget profile"""
    
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can access budget profile"
        )
    
    try:
        designation_str = current_user.designation or "associate"
        work_city = current_user.work_city or "Mumbai"
        
        designation = budget_service.get_designation_from_string(designation_str)
        
        profile = budget_service.create_employee_budget_profile(
            employee_id=current_user.user_id,
            designation=designation,
            work_city=work_city
        )
        
        return {
            "success": True,
            "profile": profile.dict(),
            "message": "Budget profile retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving budget profile for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve budget profile: {str(e)}"
        )

@router.get("/city-tiers", response_model=Dict)
async def get_city_tiers():
    """Get list of cities and their tier classifications"""
    
    try:
        city_mappings = {}
        for city_key, city_mapping in budget_service.city_mappings.items():
            city_mappings[city_key] = {
                "city_name": city_mapping.city_name,
                "city_tier": city_mapping.city_tier.value,
                "state": city_mapping.state,
                "region": city_mapping.region
            }
        
        return {
            "success": True,
            "city_mappings": city_mappings,
            "tier_descriptions": {
                "tier_1": "Metro cities with highest allowances (Mumbai, Delhi, Bangalore, etc.)",
                "tier_2": "Major cities with moderate allowances",
                "tier_3": "Smaller cities and towns with basic allowances"
            },
            "message": "City tier mappings retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving city tiers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve city tiers: {str(e)}"
        )

@router.get("/designations", response_model=Dict)
async def get_designation_hierarchy():
    """Get list of employee designations and their hierarchy"""
    
    try:
        designations = [
            {"value": "intern", "label": "Intern", "level": 1},
            {"value": "associate", "label": "Associate", "level": 2},
            {"value": "senior_associate", "label": "Senior Associate", "level": 3},
            {"value": "manager", "label": "Manager", "level": 4},
            {"value": "senior_manager", "label": "Senior Manager", "level": 5},
            {"value": "director", "label": "Director", "level": 6},
            {"value": "senior_director", "label": "Senior Director", "level": 7},
            {"value": "vp", "label": "Vice President", "level": 8},
            {"value": "svp", "label": "Senior Vice President", "level": 9},
        ]
        
        return {
            "success": True,
            "designations": designations,
            "message": "Designation hierarchy retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving designations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve designations: {str(e)}"
        )

@router.post("/refresh-session", response_model=Dict)
async def refresh_budget_session(
    travel_city: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Refresh employee's budget session with updated travel city"""
    
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can refresh budget session"
        )
    
    try:
        designation_str = current_user.designation or "associate"
        work_city = current_user.work_city or "Mumbai"
        
        designation = budget_service.get_designation_from_string(designation_str)
        
        # Create new session
        session = budget_service.create_fund_caps_session(
            employee_id=current_user.user_id,
            designation=designation,
            work_city=work_city,
            travel_city=travel_city
        )
        
        return {
            "success": True,
            "session_id": session.session_id,
            "designation": session.designation.value,
            "work_city_tier": session.work_city_tier.value,
            "travel_city_tier": session.travel_city_tier.value if session.travel_city_tier else None,
            "fund_caps": session.fund_caps,
            "expires_at": session.expires_at,
            "message": "Budget session refreshed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error refreshing budget session for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not refresh budget session: {str(e)}"
        )

@router.get("/expense-summary", response_model=Dict)
async def get_expense_summary_with_budget(current_user: TokenData = Depends(get_current_user)):
    """Get employee's expense summary with budget comparison"""
    
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can access expense summary"
        )
    
    try:
        # Get active session
        session = budget_service.get_active_session(current_user.user_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active budget session found. Please login again."
            )
        
        # TODO: Integrate with actual expense data from database
        # For now, return budget caps structure
        
        expense_summary = {
            "employee_id": current_user.user_id,
            "designation": session.designation.value,
            "work_city_tier": session.work_city_tier.value,
            "budget_caps": session.fund_caps,
            "current_usage": {
                # These would be calculated from actual expense records
                "travel": {"daily": 0, "monthly": 0},
                "hotel": {"daily": 0, "monthly": 0},
                "food": {"daily": 0, "monthly": 0},
                "local_transport": {"daily": 0, "monthly": 0},
                "miscellaneous": {"daily": 0, "monthly": 0},
            },
            "remaining_budget": {
                # These would be calculated: budget_caps - current_usage
                expense_type: {
                    "daily": float(caps["daily_limit"]),
                    "monthly": float(caps["monthly_limit"])
                }
                for expense_type, caps in session.fund_caps.items()
            }
        }
        
        return {
            "success": True,
            "summary": expense_summary,
            "message": "Expense summary with budget retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving expense summary for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve expense summary: {str(e)}"
        )

# Manager-only endpoints
@router.get("/team-budget-overview", response_model=Dict)
async def get_team_budget_overview(current_user: TokenData = Depends(get_current_user)):
    """Get budget overview for all team members (Manager only)"""
    
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can access team budget overview"
        )
    
    try:
        # TODO: Implement team budget overview
        # This would fetch all employees under this manager and their budget status
        
        return {
            "success": True,
            "message": "Team budget overview feature coming soon",
            "manager_id": current_user.user_id
        }
        
    except Exception as e:
        logger.error(f"Error retrieving team budget overview for manager {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve team budget overview: {str(e)}"
        )

@router.post("/cleanup-sessions", response_model=Dict)
async def cleanup_expired_sessions():
    """Cleanup expired budget sessions (Admin endpoint)"""
    
    try:
        budget_service.cleanup_expired_sessions()
        
        return {
            "success": True,
            "message": "Expired sessions cleaned up successfully"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not cleanup expired sessions: {str(e)}"
        )