from fastapi import APIRouter, HTTPException, Depends, Query
from models.bill_postgres_models import BillListResponse, BillResponse, EmployeeBillSummary
from models.user_models import TokenData
from dependencies.auth_dependencies import get_current_manager
from database import db_manager
from services.manager_service import manager_service
import logging
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manager", tags=["Manager Operations"])

# Response models for employee data from MongoDB
class EmployeeInfo(BaseModel):
    id: str
    name: str = ""
    username: str = ""
    email: str = ""
    department: str = ""
    registration_date: str = ""
    total_bills: int = 0
    total_amount: float = 0.0
    pending_bills: int = 0
    approved_bills: int = 0
    rejected_bills: int = 0
    avg_amount: float = 0.0

@router.get("/team-overview", response_model=List[EmployeeInfo])
async def get_team_overview(
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Get overview of all employees under the manager from MongoDB Atlas.
    Returns employee data with name, username, email, and registration date.
    Only managers can access this endpoint.
    """
    try:
        # Get employees from MongoDB and enhance with PostgreSQL bill data
        employees = await manager_service.get_team_employees(current_user.user_id)
        
        # Convert to response format
        employee_list = []
        for emp in employees:
            employee_info = EmployeeInfo(
                id=emp["id"],
                name=emp.get("name") or "",
                username=emp.get("username") or "",
                email=emp.get("email") or "",
                department=emp.get("department") or "",
                registration_date=emp.get("registration_date") or "",
                total_bills=emp.get("total_bills", 0),
                total_amount=emp.get("total_amount", 0.0),
                pending_bills=emp.get("pending_bills", 0),
                approved_bills=emp.get("approved_bills", 0),
                rejected_bills=emp.get("rejected_bills", 0),
                avg_amount=emp.get("avg_amount", 0.0)
            )
            employee_list.append(employee_info)
        
        logger.info(f"✅ Manager {current_user.email} retrieved {len(employee_list)} employees")
        return employee_list
        
    except Exception as e:
        logger.error(f"Error fetching team overview for manager {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch team overview: {str(e)}"
        )

@router.get("/all-employees", response_model=List[EmployeeInfo])
async def get_all_employees(
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Get all registered employees from MongoDB Atlas.
    Returns all employee data with name, username, email, and registration date.
    Only managers can access this endpoint.
    """
    try:
        # Get all employees from MongoDB and enhance with PostgreSQL bill data
        employees = await manager_service.get_all_employees()
        
        # Convert to response format
        employee_list = []
        for emp in employees:
            employee_info = EmployeeInfo(
                id=emp["id"],
                name=emp.get("name") or "",
                username=emp.get("username") or "",
                email=emp.get("email") or "",
                department=emp.get("department") or "",
                registration_date=emp.get("registration_date") or "",
                total_bills=emp.get("total_bills", 0),
                total_amount=emp.get("total_amount", 0.0),
                pending_bills=emp.get("pending_bills", 0),
                approved_bills=emp.get("approved_bills", 0),
                rejected_bills=emp.get("rejected_bills", 0),
                avg_amount=emp.get("avg_amount", 0.0)
            )
            employee_list.append(employee_info)
        
        logger.info(f"✅ Manager {current_user.email} retrieved {len(employee_list)} total employees")
        return employee_list
        
    except Exception as e:
        logger.error(f"Error fetching all employees for manager {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch all employees: {str(e)}"
        )

@router.get("/employee/{employee_id}/bills", response_model=BillListResponse)
async def get_employee_bills(
    employee_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Get bills for a specific employee under the manager.
    Only managers can access employee bills.
    """
    try:
        # Verify that the employee is under this manager
        employee_check = await db_manager.execute_query(
            "SELECT id FROM app_users WHERE id = $1 AND manager_id = $2",
            employee_id, int(current_user.user_id)
        )
        
        if not employee_check:
            raise HTTPException(
                status_code=404,
                detail="Employee not found or not under your management"
            )
        
        offset = (page - 1) * page_size
        
        # Build query with optional status filter
        if status:
            bills_query = """
            SELECT b.*, u.username, u.full_name as employee_name, u.email as employee_email, u.department
            FROM app_bills b
            JOIN app_users u ON b.employee_id = u.id
            WHERE b.employee_id = $1 AND b.status = $2
            ORDER BY b.created_at DESC
            LIMIT $3 OFFSET $4
            """
            count_query = "SELECT COUNT(*) as count FROM app_bills WHERE employee_id = $1 AND status = $2"
            bills = await db_manager.execute_query(bills_query, employee_id, status, page_size, offset)
            total_count_result = await db_manager.execute_query(count_query, employee_id, status)
        else:
            bills_query = """
            SELECT b.*, u.username, u.full_name as employee_name, u.email as employee_email, u.department
            FROM app_bills b
            JOIN app_users u ON b.employee_id = u.id
            WHERE b.employee_id = $1
            ORDER BY b.created_at DESC
            LIMIT $2 OFFSET $3
            """
            count_query = "SELECT COUNT(*) as count FROM app_bills WHERE employee_id = $1"
            bills = await db_manager.execute_query(bills_query, employee_id, page_size, offset)
            total_count_result = await db_manager.execute_query(count_query, employee_id)
        
        total_count = total_count_result[0]['count'] if total_count_result else 0
        total_pages = (total_count + page_size - 1) // page_size
        
        bill_responses = [BillResponse(**bill) for bill in bills]
        
        return BillListResponse(
            bills=bill_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee bills: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch employee bills: {str(e)}"
        )

@router.get("/pending-bills", response_model=BillListResponse)
async def get_pending_bills(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Get all pending bills from employees under the manager.
    Only managers can access this endpoint.
    """
    try:
        offset = (page - 1) * page_size
        
        bills_query = """
        SELECT b.*, u.username, u.full_name as employee_name, u.email as employee_email, u.department
        FROM app_bills b
        JOIN app_users u ON b.employee_id = u.id
        WHERE u.manager_id = $1 AND b.status = 'pending'
        ORDER BY b.created_at ASC
        LIMIT $2 OFFSET $3
        """
        
        count_query = """
        SELECT COUNT(*) as count FROM app_bills b
        JOIN app_users u ON b.employee_id = u.id
        WHERE u.manager_id = $1 AND b.status = 'pending'
        """
        
        bills = await db_manager.execute_query(bills_query, int(current_user.user_id), page_size, offset)
        total_count_result = await db_manager.execute_query(count_query, int(current_user.user_id))
        
        total_count = total_count_result[0]['count'] if total_count_result else 0
        total_pages = (total_count + page_size - 1) // page_size
        
        bill_responses = [BillResponse(**bill) for bill in bills]
        
        return BillListResponse(
            bills=bill_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error fetching pending bills for manager {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch pending bills: {str(e)}"
        )

@router.post("/bills/{bill_id}/approve")
async def approve_bill(
    bill_id: int,
    remarks: Optional[str] = None,
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Approve a bill.
    Only managers can approve bills from their team.
    """
    try:
        # Check if bill exists and belongs to manager's team
        bill_check = await db_manager.execute_query(
            """SELECT b.id, u.full_name as employee_name FROM app_bills b
               JOIN app_users u ON b.employee_id = u.id
               WHERE b.id = $1 AND u.manager_id = $2""",
            bill_id, int(current_user.user_id)
        )
        
        if not bill_check:
            raise HTTPException(
                status_code=404,
                detail="Bill not found or access denied"
            )
        
        # Update bill status to approved
        success = await db_manager.update_bill_status(bill_id, 'approved')
        
        if remarks:
            await db_manager.execute_command(
                "UPDATE app_bills SET remarks = $1 WHERE id = $2",
                remarks, bill_id
            )
        
        if success:
            employee_name = bill_check[0]['employee_name']
            return {
                "message": f"Bill approved successfully for {employee_name}",
                "bill_id": bill_id,
                "status": "approved",
                "approved_by": current_user.full_name or current_user.username
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to approve bill"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving bill: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve bill: {str(e)}"
        )

@router.post("/bills/{bill_id}/reject")
async def reject_bill(
    bill_id: int,
    remarks: Optional[str] = None,
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Reject a bill.
    Only managers can reject bills from their team.
    """
    try:
        # Check if bill exists and belongs to manager's team
        bill_check = await db_manager.execute_query(
            """SELECT b.id, u.full_name as employee_name FROM app_bills b
               JOIN app_users u ON b.employee_id = u.id
               WHERE b.id = $1 AND u.manager_id = $2""",
            bill_id, int(current_user.user_id)
        )
        
        if not bill_check:
            raise HTTPException(
                status_code=404,
                detail="Bill not found or access denied"
            )
        
        # Update bill status to rejected
        success = await db_manager.update_bill_status(bill_id, 'rejected')
        
        if remarks:
            await db_manager.execute_command(
                "UPDATE app_bills SET remarks = $1 WHERE id = $2",
                remarks, bill_id
            )
        
        if success:
            employee_name = bill_check[0]['employee_name']
            return {
                "message": f"Bill rejected for {employee_name}",
                "bill_id": bill_id,
                "status": "rejected",
                "rejected_by": current_user.full_name or current_user.username
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reject bill"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting bill: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject bill: {str(e)}"
        )