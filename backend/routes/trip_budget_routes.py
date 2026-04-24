from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import date, datetime
from pydantic import ValidationError
import logging

from models.budget_models import (
    OfficialTrip, TripRequest, TripApproval, TripStatus, 
    TripBudgetValidationResult, ExpenseType, EmployeeDesignation
)
from models.user_models import TokenData
from services.trip_budget_service import trip_budget_service
from services.mongodb_service import mongodb_service
from dependencies.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trip-budget", tags=["Trip Budget Management"])

@router.post("/debug-request", response_model=Dict)
async def debug_trip_request(
    request: dict,
    current_user: TokenData = Depends(get_current_user)
):
    """Debug endpoint to see what data is being received"""
    logger.info(f"Raw request data: {request}")
    logger.info(f"Request type: {type(request)}")
    logger.info(f"Current user: {current_user}")
    
    return {
        "success": True,
        "received_data": request,
        "user_info": {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "designation": current_user.designation,
            "role": current_user.role
        }
    }

@router.post("/create-trip", response_model=Dict)
async def create_trip_request(
    request: TripRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Create a new official trip request"""
    
    try:
        logger.info(f"Received trip request: {request}")
        logger.info(f"Current user: {current_user.user_id}, {current_user.username}")
        # Validate dates
        if request.start_date >= request.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        if request.start_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trip start date cannot be in the past"
            )
        
        # Get employee designation
        designation_str = current_user.designation or "associate"
        logger.info(f"Employee designation string: {designation_str}")
        
        try:
            designation = trip_budget_service.get_designation_from_string(designation_str)
            logger.info(f"Converted designation: {designation}")
        except Exception as e:
            logger.error(f"Error converting designation: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid designation: {designation_str}"
            )
        
        # Create trip request
        try:
            trip = trip_budget_service.create_trip_request(
                employee_id=current_user.user_id,
                employee_name=current_user.full_name or current_user.username,
                designation=designation,
                trip_purpose=request.trip_purpose,
                destination_city=request.destination_city,
                start_date=request.start_date,
                end_date=request.end_date
            )
            logger.info(f"Trip created successfully: {trip.trip_id}")
        except Exception as e:
            logger.error(f"Error creating trip: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create trip: {str(e)}"
            )
        
        # TODO: Send notification to manager about new trip request
        # This would integrate with your notification system
        logger.info(f"Trip request {trip.trip_id} created by {current_user.username} - requires manager approval")
        
        return {
            "success": True,
            "trip_id": trip.trip_id,
            "message": f"Trip request created successfully for {request.destination_city}",
            "trip_details": {
                "trip_id": trip.trip_id,
                "destination": trip.destination_city,
                "destination_tier": trip.destination_tier.value,
                "duration_days": trip.duration_days,
                "start_date": trip.start_date.isoformat(),
                "end_date": trip.end_date.isoformat(),
                "status": trip.status.value,
                "allocated_budget": {k: float(v) for k, v in trip.allocated_budget.items()},
                "total_allocated": float(trip.total_allocated)
            }
        }
        
    except ValidationError as e:
        logger.error(f"Validation error creating trip request: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating trip request for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create trip request: {str(e)}"
        )

@router.get("/my-trips", response_model=Dict)
async def get_my_trips(
    status_filter: Optional[str] = Query(None, description="Filter by trip status"),
    current_user: TokenData = Depends(get_current_user)
):
    """Get all trips for the current employee"""
    
    try:
        # Parse status filter
        trip_status = None
        if status_filter:
            try:
                trip_status = TripStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter. Valid values: {[s.value for s in TripStatus]}"
                )
        
        # Get employee trips
        trips = trip_budget_service.get_employee_trips(current_user.user_id, trip_status)
        
        # Format trips for response
        formatted_trips = []
        for trip in trips:
            formatted_trips.append({
                "trip_id": trip.trip_id,
                "purpose": trip.trip_purpose,
                "destination": trip.destination_city,
                "destination_tier": trip.destination_tier.value,
                "start_date": trip.start_date.isoformat(),
                "end_date": trip.end_date.isoformat(),
                "duration_days": trip.duration_days,
                "status": trip.status.value,
                "allocated_budget": {k: float(v) for k, v in trip.allocated_budget.items()},
                "total_allocated": float(trip.total_allocated),
                "expenses_submitted": float(trip.expenses_submitted),
                "remaining_budget": float(trip.remaining_budget),
                "approved_by": trip.approved_by,
                "approved_at": trip.approved_at.isoformat() if trip.approved_at else None,
                "created_at": trip.created_at.isoformat()
            })
        
        return {
            "success": True,
            "trips": formatted_trips,
            "total_trips": len(formatted_trips),
            "message": f"Retrieved {len(formatted_trips)} trips"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving trips for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve trips: {str(e)}"
        )

@router.get("/active-trip", response_model=Dict)
async def get_active_trip(current_user: TokenData = Depends(get_current_user)):
    """Get current active trip session for expense submission"""
    
    try:
        # Get active trip session
        session = trip_budget_service.get_active_trip_session(current_user.user_id)
        
        if not session:
            return {
                "success": False,
                "message": "No active trip found. You can only submit expenses during approved company trips.",
                "active_trip": None
            }
        
        # Get trip details
        trip = trip_budget_service.get_trip_by_id(session.trip_id)
        
        return {
            "success": True,
            "message": "Active trip session found",
            "active_trip": {
                "trip_id": session.trip_id,
                "destination": trip.destination_city if trip else "Unknown",
                "destination_tier": session.destination_tier.value,
                "trip_start": session.trip_start.isoformat(),
                "trip_end": session.trip_end.isoformat(),
                "allocated_budgets": {k: float(v) for k, v in session.allocated_budgets.items()},
                "used_budgets": {k: float(v) for k, v in session.used_budgets.items()},
                "remaining_budgets": {k: float(v) for k, v in session.remaining_budgets.items()},
                "is_active": session.is_active
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving active trip for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve active trip: {str(e)}"
        )

@router.post("/validate-expense", response_model=TripBudgetValidationResult)
async def validate_trip_expense(
    expense_type: str,
    amount: float,
    current_user: TokenData = Depends(get_current_user)
):
    """Validate an expense against active trip budget"""
    
    try:
        # Convert expense type string to enum
        try:
            expense_type_enum = ExpenseType(expense_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid expense type: {expense_type}. Valid types: {[e.value for e in ExpenseType]}"
            )
        
        # Validate expense
        validation_result = trip_budget_service.validate_trip_expense(
            employee_id=current_user.user_id,
            expense_type=expense_type_enum,
            amount=Decimal(str(amount))
        )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating trip expense for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not validate expense: {str(e)}"
        )

@router.get("/budget-calculator", response_model=Dict)
async def calculate_trip_budget(
    destination_city: str,
    start_date: date,
    end_date: date,
    current_user: TokenData = Depends(get_current_user)
):
    """Calculate budget allocation for a potential trip"""
    
    try:
        # Validate dates
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        duration_days = (end_date - start_date).days + 1
        
        # Get employee designation
        designation_str = current_user.designation or "associate"
        designation = trip_budget_service.get_designation_from_string(designation_str)
        
        # Calculate budget
        budget_allocation = trip_budget_service.calculate_trip_budget(
            designation=designation,
            destination_city=destination_city,
            duration_days=duration_days
        )
        
        total_budget = sum(budget_allocation.values())
        city_tier = trip_budget_service.get_city_tier(destination_city)
        
        return {
            "success": True,
            "calculation": {
                "destination_city": destination_city,
                "city_tier": city_tier.value,
                "duration_days": duration_days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "designation": designation.value,
                "budget_breakdown": {k: float(v) for k, v in budget_allocation.items()},
                "total_budget": float(total_budget)
            },
            "message": f"Budget calculated for {duration_days}-day trip to {destination_city}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating trip budget for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not calculate trip budget: {str(e)}"
        )

@router.get("/city-tiers", response_model=Dict)
async def get_city_tiers():
    """Get list of cities and their tier classifications"""
    
    try:
        city_mappings = {}
        for city_key, city_mapping in trip_budget_service.city_mappings.items():
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

@router.post("/complete-trip", response_model=Dict)
async def complete_trip(
    trip_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Mark a trip as completed"""
    
    try:
        # Complete the trip
        trip = await trip_budget_service.complete_trip(trip_id)
        
        logger.info(f"Trip {trip_id} completed by employee {current_user.user_id}")
        
        return {
            "success": True,
            "trip_id": trip_id,
            "message": f"Trip {trip_id} marked as completed successfully",
            "trip_details": {
                "trip_id": trip.trip_id,
                "status": trip.status.value,
                "destination": trip.destination_city,
                "duration_days": trip.duration_days,
                "total_allocated": float(trip.total_allocated),
                "expenses_submitted": float(trip.expenses_submitted)
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error completing trip {trip_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not complete trip: {str(e)}"
        )

@router.post("/submit-trip", response_model=Dict)
async def submit_trip_for_approval(
    request: dict,
    current_user: TokenData = Depends(get_current_user)
):
    """Submit a completed trip with all bills for manager approval"""
    
    try:
        trip_id = request.get('trip_id')
        submission_notes = request.get('submission_notes')
        
        if not trip_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="trip_id is required"
            )
        
        # Get PostgreSQL user ID from MongoDB user ID
        from database import db_manager
        
        # First, get the user's email from MongoDB to find their PostgreSQL ID
        mongo_user = mongodb_service.find_user_by_id(current_user.user_id)
        if not mongo_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get PostgreSQL user ID by email
        pg_user = await db_manager.get_user_by_email(mongo_user.get('email'))
        if not pg_user:
            # Sync user from MongoDB to PostgreSQL if not exists
            pg_user_id = await db_manager.sync_user_from_mongodb(mongo_user)
        else:
            pg_user_id = pg_user['id']
        
        # Get manager ID (for now use default, should be from user profile)
        manager_id = pg_user.get('manager_id', 1) if pg_user else 1
        
        # Submit trip for approval
        result = await trip_budget_service.submit_trip_for_approval(
            trip_id=trip_id,
            employee_id=pg_user_id,
            manager_id=manager_id,
            submission_notes=submission_notes
        )
        
        logger.info(f"Trip {trip_id} submitted for approval by employee {current_user.user_id}")
        
        return {
            "success": True,
            **result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting trip for approval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not submit trip for approval: {str(e)}"
        )

# Manager-only endpoints
@router.get("/pending-requests", response_model=Dict)
async def get_pending_trip_requests(
    current_user: TokenData = Depends(get_current_user)
):
    """Get all pending trip requests for manager approval"""
    
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can view pending trip requests"
        )
    
    try:
        # Get all pending trips (in a real system, this would filter by manager's team)
        all_trips = list(trip_budget_service.official_trips.values())
        pending_trips = [trip for trip in all_trips if trip.status == TripStatus.PENDING]
        
        # Format trips for response
        formatted_trips = []
        for trip in pending_trips:
            formatted_trips.append({
                "trip_id": trip.trip_id,
                "employee_id": trip.employee_id,
                "employee_name": trip.employee_name,
                "designation": trip.designation.value,
                "purpose": trip.trip_purpose,
                "destination": trip.destination_city,
                "destination_tier": trip.destination_tier.value,
                "start_date": trip.start_date.isoformat(),
                "end_date": trip.end_date.isoformat(),
                "duration_days": trip.duration_days,
                "status": trip.status.value,
                "allocated_budget": {k: float(v) for k, v in trip.allocated_budget.items()},
                "total_allocated": float(trip.total_allocated),
                "created_at": trip.created_at.isoformat()
            })
        
        return {
            "success": True,
            "pending_requests": formatted_trips,
            "total_pending": len(formatted_trips),
            "message": f"Retrieved {len(formatted_trips)} pending trip requests"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving pending trip requests for manager {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve pending requests: {str(e)}"
        )

@router.post("/approve-trip", response_model=Dict)
async def approve_trip_request(
    request: TripApproval,
    current_user: TokenData = Depends(get_current_user)
):
    """Approve a trip request (Manager only)"""
    
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can approve trip requests"
        )
    
    try:
        # Convert budget adjustments to Decimal if provided
        decimal_adjustments = None
        if request.budget_adjustments:
            decimal_adjustments = {k: Decimal(str(v)) for k, v in request.budget_adjustments.items()}
        
        # Approve trip
        trip = await trip_budget_service.approve_trip(
            trip_id=request.trip_id,
            approved_by=current_user.user_id,
            budget_adjustments=decimal_adjustments
        )
        
        return {
            "success": True,
            "trip_id": request.trip_id,
            "message": f"Trip request approved successfully",
            "approved_trip": {
                "trip_id": trip.trip_id,
                "employee_name": trip.employee_name,
                "destination": trip.destination_city,
                "start_date": trip.start_date.isoformat(),
                "end_date": trip.end_date.isoformat(),
                "status": trip.status.value,
                "allocated_budget": {k: float(v) for k, v in trip.allocated_budget.items()},
                "total_allocated": float(trip.total_allocated),
                "approved_by": trip.approved_by,
                "approved_at": trip.approved_at.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error approving trip {trip_id} by manager {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not approve trip: {str(e)}"
        )

@router.post("/reject-trip", response_model=Dict)
async def reject_trip_request(
    request: dict,
    current_user: TokenData = Depends(get_current_user)
):
    """Reject a trip request (Manager only)"""
    
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can reject trip requests"
        )
    
    try:
        trip_id = request.get('trip_id')
        reason = request.get('reason')
        
        if not trip_id or not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trip ID and rejection reason are required"
            )
        
        # Reject trip
        trip = trip_budget_service.reject_trip(
            trip_id=trip_id,
            rejected_by=current_user.user_id,
            rejection_reason=reason
        )
        
        return {
            "success": True,
            "trip_id": trip_id,
            "message": f"Trip request rejected successfully",
            "rejected_trip": {
                "trip_id": trip.trip_id,
                "employee_name": trip.employee_name,
                "destination": trip.destination_city,
                "status": trip.status.value,
                "rejected_by": trip.rejected_by,
                "rejected_at": trip.rejected_at.isoformat() if trip.rejected_at else None,
                "rejection_reason": trip.rejection_reason
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rejecting trip {request.get('trip_id')} by manager {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not reject trip: {str(e)}"
        )

@router.post("/activate-trip", response_model=Dict)
async def activate_trip_for_expenses(
    trip_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Activate an approved trip for expense submission"""
    
    try:
        # Get trip details
        trip = trip_budget_service.get_trip_by_id(trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Check if user owns the trip or is a manager
        if trip.employee_id != current_user.user_id and current_user.role != "manager":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only activate your own trips"
            )
        
        # Activate trip
        session = trip_budget_service.activate_trip(trip_id)
        
        return {
            "success": True,
            "trip_id": trip_id,
            "message": f"Trip activated successfully. You can now submit expenses.",
            "active_session": {
                "trip_id": session.trip_id,
                "destination_tier": session.destination_tier.value,
                "trip_start": session.trip_start.isoformat(),
                "trip_end": session.trip_end.isoformat(),
                "allocated_budgets": {k: float(v) for k, v in session.allocated_budgets.items()},
                "remaining_budgets": {k: float(v) for k, v in session.remaining_budgets.items()}
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error activating trip {trip_id} for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not activate trip: {str(e)}"
        )

@router.post("/complete-trip", response_model=Dict)
async def complete_trip(
    trip_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Mark a trip as completed"""
    
    try:
        # Get trip details
        trip = trip_budget_service.get_trip_by_id(trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Check if user owns the trip or is a manager
        if trip.employee_id != current_user.user_id and current_user.role != "manager":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only complete your own trips"
            )
        
        # Complete trip
        completed_trip = trip_budget_service.complete_trip(trip_id)
        
        return {
            "success": True,
            "trip_id": trip_id,
            "message": f"Trip marked as completed",
            "completed_trip": {
                "trip_id": completed_trip.trip_id,
                "status": completed_trip.status.value,
                "total_allocated": float(completed_trip.total_allocated),
                "expenses_submitted": float(completed_trip.expenses_submitted),
                "remaining_budget": float(completed_trip.remaining_budget)
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error completing trip {trip_id} for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not complete trip: {str(e)}"
        )

@router.post("/cleanup-sessions", response_model=Dict)
async def cleanup_expired_sessions():
    """Cleanup expired trip sessions (Admin endpoint)"""
    
    try:
        trip_budget_service.cleanup_expired_sessions()
        
        return {
            "success": True,
            "message": "Expired trip sessions cleaned up successfully"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not cleanup expired sessions: {str(e)}"
        )

# New Manager endpoints for Trip Submissions
@router.get("/pending-trip-submissions", response_model=Dict)
async def get_pending_trip_submissions(
    current_user: TokenData = Depends(get_current_user)
):
    """Get all pending trip submissions for manager approval"""
    
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can view pending trip submissions"
        )
    
    try:
        from database import db_manager
        
        # Get manager's PostgreSQL ID
        manager_pg_user = await db_manager.get_user_by_email(current_user.email)
        if not manager_pg_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found in database"
            )
        
        manager_id = manager_pg_user['id']
        
        # Get pending submissions
        submissions = await db_manager.get_pending_trip_submissions(manager_id)
        
        # If no submissions found for this specific manager, get all pending submissions
        # This handles cases where manager_id is not properly set
        if not submissions:
            logger.info(f"No submissions found for manager {manager_id}, trying all pending submissions")
            submissions = await db_manager.get_all_pending_trip_submissions()
        
        formatted_submissions = []
        for submission in submissions:
            formatted_submissions.append({
                "submission_id": submission['id'],
                "trip_id": submission['trip_id'],
                "employee_id": submission['employee_id'],
                "employee_name": submission['employee_name'],
                "trip_purpose": submission['trip_purpose'],
                "destination_city": submission['destination_city'],
                "start_date": submission['start_date'].isoformat() if submission['start_date'] else None,
                "end_date": submission['end_date'].isoformat() if submission['end_date'] else None,
                "duration_days": submission['duration_days'],
                "total_bills": submission['actual_bills_count'],
                "total_amount": float(submission['actual_total_amount']),
                "allocated_budget": float(submission['allocated_budget']),
                "budget_utilization": float(submission['budget_utilization']),
                "submitted_at": submission['submitted_at'].isoformat() if submission['submitted_at'] else None
            })
        
        return {
            "success": True,
            "pending_submissions": formatted_submissions,
            "total_pending": len(formatted_submissions),
            "message": f"Retrieved {len(formatted_submissions)} pending trip submissions"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pending trip submissions for manager {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve pending submissions: {str(e)}"
        )

@router.get("/trip-submission-details/{submission_id}", response_model=Dict)
async def get_trip_submission_details(
    submission_id: int,
    current_user: TokenData = Depends(get_current_user)
):
    """Get detailed information about a trip submission including all bills"""
    
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can view trip submission details"
        )
    
    try:
        from database import db_manager
        
        # Get submission details
        submission_query = """
        SELECT * FROM app_trip_submissions WHERE id = $1
        """
        submission_result = await db_manager.execute_query(submission_query, submission_id)
        
        if not submission_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip submission not found"
            )
        
        submission = submission_result[0]
        
        # Get all bills for this trip
        trip_bills = await db_manager.get_trip_bills(submission['trip_id'])
        
        formatted_bills = []
        for bill in trip_bills:
            formatted_bills.append({
                "bill_id": bill['id'],
                "filename": bill['filename'],
                "date": bill['date'].isoformat() if bill['date'] else None,
                "vendor": bill['vendor'],
                "category": bill['category'],
                "amount": float(bill['amount']),
                "subtotal": float(bill['subtotal']) if bill['subtotal'] else None,
                "tax": float(bill['tax']) if bill['tax'] else None,
                "currency": bill['currency'],
                "confidence_score": float(bill['confidence_score']) if bill['confidence_score'] else None,
                "status": bill['status'],
                "created_at": bill['created_at'].isoformat() if bill['created_at'] else None
            })
        
        return {
            "success": True,
            "submission_details": {
                "submission_id": submission['id'],
                "trip_id": submission['trip_id'],
                "employee_name": submission['employee_name'],
                "trip_purpose": submission['trip_purpose'],
                "destination_city": submission['destination_city'],
                "start_date": submission['start_date'].isoformat() if submission['start_date'] else None,
                "end_date": submission['end_date'].isoformat() if submission['end_date'] else None,
                "duration_days": submission['duration_days'],
                "total_bills": len(formatted_bills),
                "total_amount": sum(bill['amount'] for bill in formatted_bills),
                "allocated_budget": float(submission['allocated_budget']),
                "budget_utilization": float(submission['budget_utilization']),
                "submission_status": submission['submission_status'],
                "submitted_at": submission['submitted_at'].isoformat() if submission['submitted_at'] else None
            },
            "bills": formatted_bills,
            "message": f"Retrieved details for trip submission {submission_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving trip submission details {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve submission details: {str(e)}"
        )

@router.post("/approve-trip-submission", response_model=Dict)
async def approve_trip_submission(
    request: dict,
    current_user: TokenData = Depends(get_current_user)
):
    """Approve a trip submission and all associated bills"""
    
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can approve trip submissions"
        )
    
    try:
        submission_id = request.get('submission_id')
        comments = request.get('comments', '')
        
        logger.info(f"Received approval request: submission_id={submission_id}, type={type(submission_id)}")
        
        if not submission_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="submission_id is required"
            )
        
        # Convert to int if it's a string
        try:
            submission_id = int(submission_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="submission_id must be a valid integer"
            )
        
        from database import db_manager
        
        # Get manager's PostgreSQL ID
        manager_pg_user = await db_manager.get_user_by_email(current_user.email)
        if not manager_pg_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found in database"
            )
        
        manager_id = manager_pg_user['id']
        
        # Approve the submission
        success = await db_manager.approve_trip_submission(submission_id, manager_id, comments)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to approve trip submission"
            )
        
        logger.info(f"Trip submission {submission_id} approved by manager {current_user.user_id}")
        
        return {
            "success": True,
            "submission_id": submission_id,
            "message": "Trip submission and all associated bills approved successfully",
            "approved_by": current_user.full_name or current_user.username,
            "comments": comments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving trip submission {request.get('submission_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not approve trip submission: {str(e)}"
        )

@router.post("/reject-trip-submission", response_model=Dict)
async def reject_trip_submission(
    request: dict,
    current_user: TokenData = Depends(get_current_user)
):
    """Reject a trip submission and all associated bills"""
    
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can reject trip submissions"
        )
    
    try:
        submission_id = request.get('submission_id')
        reason = request.get('reason', '')
        
        if not submission_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="submission_id is required"
            )
        
        if not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="rejection reason is required"
            )
        
        from database import db_manager
        
        # Get manager's PostgreSQL ID
        manager_pg_user = await db_manager.get_user_by_email(current_user.email)
        if not manager_pg_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found in database"
            )
        
        manager_id = manager_pg_user['id']
        
        # Reject the submission
        success = await db_manager.reject_trip_submission(submission_id, manager_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reject trip submission"
            )
        
        logger.info(f"Trip submission {submission_id} rejected by manager {current_user.user_id}")
        
        return {
            "success": True,
            "submission_id": submission_id,
            "message": "Trip submission and all associated bills rejected",
            "rejected_by": current_user.full_name or current_user.username,
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting trip submission {request.get('submission_id')}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not reject trip submission: {str(e)}"
        )

# Completed Trips Endpoints

@router.get("/completed-trips", response_model=Dict)
async def get_completed_trips(
    current_user: TokenData = Depends(get_current_user)
):
    """Get completed trips for the current employee"""
    
    try:
        from database import db_manager
        from services.mongodb_service import mongodb_service
        
        # Get MongoDB user details
        mongo_user = mongodb_service.find_user_by_id(current_user.user_id)
        if not mongo_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get PostgreSQL user ID
        pg_user = await db_manager.get_user_by_email(mongo_user.get('email'))
        if not pg_user:
            # Sync user if not exists
            pg_user_id = await db_manager.sync_user_from_mongodb(mongo_user)
        else:
            pg_user_id = pg_user['id']
        
        if not pg_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not find or create user in database"
            )
        
        # Get completed trips
        completed_trips = await db_manager.get_completed_trips_by_employee(pg_user_id)
        
        formatted_trips = []
        for trip in completed_trips:
            formatted_trips.append({
                "trip_id": trip['trip_id'],
                "trip_purpose": trip['trip_purpose'],
                "destination_city": trip['destination_city'],
                "start_date": trip['start_date'].isoformat() if trip['start_date'] else None,
                "end_date": trip['end_date'].isoformat() if trip['end_date'] else None,
                "duration_days": trip['duration_days'],
                "designation": trip['designation'],
                "city_tier": trip['city_tier'],
                "allocated_budget": float(trip['allocated_budget']) if trip['allocated_budget'] else 0,
                "total_bills": trip['total_bills'],
                "total_amount": float(trip['total_amount']) if trip['total_amount'] else 0,
                "actual_bills_count": trip.get('actual_bills_count', 0),
                "actual_total_amount": float(trip.get('actual_total_amount', 0)),
                "budget_utilization": float(trip['budget_utilization']) if trip['budget_utilization'] else 0,
                "trip_status": trip['trip_status'],
                "submission_status": trip['submission_status'],
                "completed_at": trip['completed_at'].isoformat() if trip['completed_at'] else None,
                "submitted_at": trip['submitted_at'].isoformat() if trip['submitted_at'] else None,
                "approved_at": trip['approved_at'].isoformat() if trip['approved_at'] else None,
                "approval_comments": trip['approval_comments'],
                "rejection_reason": trip['rejection_reason']
            })
        
        return {
            "success": True,
            "completed_trips": formatted_trips,
            "total_count": len(formatted_trips)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching completed trips for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch completed trips: {str(e)}"
        )

@router.get("/manager/completed-trips", response_model=Dict)
async def get_manager_completed_trips(
    current_user: TokenData = Depends(get_current_user)
):
    """Get all completed trips for manager view"""
    
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can view all completed trips"
        )
    
    try:
        from database import db_manager
        
        # Get manager's PostgreSQL ID
        manager_pg_user = await db_manager.get_user_by_email(current_user.email)
        if not manager_pg_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found in database"
            )
        
        manager_id = manager_pg_user['id']
        
        # Get all completed trips for this manager
        completed_trips = await db_manager.get_all_completed_trips_for_manager(manager_id)
        
        formatted_trips = []
        for trip in completed_trips:
            formatted_trips.append({
                "trip_id": trip['trip_id'],
                "employee_name": trip['employee_name'],
                "trip_purpose": trip['trip_purpose'],
                "destination_city": trip['destination_city'],
                "start_date": trip['start_date'].isoformat() if trip['start_date'] else None,
                "end_date": trip['end_date'].isoformat() if trip['end_date'] else None,
                "duration_days": trip['duration_days'],
                "designation": trip['designation'],
                "city_tier": trip['city_tier'],
                "allocated_budget": float(trip['allocated_budget']) if trip['allocated_budget'] else 0,
                "total_bills": trip['total_bills'],
                "total_amount": float(trip['total_amount']) if trip['total_amount'] else 0,
                "actual_bills_count": trip.get('actual_bills_count', 0),
                "actual_total_amount": float(trip.get('actual_total_amount', 0)),
                "budget_utilization": float(trip['budget_utilization']) if trip['budget_utilization'] else 0,
                "trip_status": trip['trip_status'],
                "submission_status": trip['submission_status'],
                "completed_at": trip['completed_at'].isoformat() if trip['completed_at'] else None,
                "submitted_at": trip['submitted_at'].isoformat() if trip['submitted_at'] else None,
                "approved_at": trip['approved_at'].isoformat() if trip['approved_at'] else None,
                "approval_comments": trip['approval_comments'],
                "rejection_reason": trip['rejection_reason']
            })
        
        return {
            "success": True,
            "completed_trips": formatted_trips,
            "total_count": len(formatted_trips)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching completed trips for manager {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch completed trips: {str(e)}"
        )