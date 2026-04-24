from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from models.bill_postgres_models import BillResponse, BillListResponse, BillStatistics, BillProcessingResult
from models.user_models import TokenData
from dependencies.auth_dependencies import get_current_user, get_current_employee, get_current_manager
from services.bill_processing_service import bill_processing_service
from services.ocr_space_service import ocr_space_service
from database import db_manager
import logging
from datetime import datetime, date
# Import MongoDB collections directly to avoid circular import
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection for user sync
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    mongo_db = mongo_client["auth_db"]
    users_collection = mongo_db["users"]
except (ConnectionFailure, ServerSelectionTimeoutError):
    users_collection = None
import time
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bills", tags=["Bill Processing with PostgreSQL"])

async def ensure_user_in_postgres(user_email: str) -> Optional[int]:
    """Ensure user exists in PostgreSQL, sync from MongoDB if needed"""
    try:
        # Check if user exists in PostgreSQL
        pg_user = await db_manager.get_user_by_email(user_email)
        if pg_user:
            return pg_user['id']
        
        # Get user from MongoDB
        if users_collection is None:
            logger.error("MongoDB users collection not available")
            return None
            
        mongo_user = users_collection.find_one({"email": user_email})
        if not mongo_user:
            logger.error(f"User {user_email} not found in MongoDB")
            return None
        
        # Sync user to PostgreSQL
        user_id = await db_manager.sync_user_from_mongodb(mongo_user)
        logger.info(f"Synced user {user_email} to PostgreSQL with ID {user_id}")
        return user_id
        
    except Exception as e:
        logger.error(f"Error ensuring user in PostgreSQL: {e}")
        return None

@router.post("/process-bill", response_model=BillProcessingResult)
async def process_bill_with_storage(
    file: UploadFile = File(...),
    submit_mode: str = Query("auto", description="Submission mode: 'auto' or 'manual'"),
    current_user: TokenData = Depends(get_current_employee)
):
    """
    Process uploaded bill: Extract text via OCR, parse financial data, and store in PostgreSQL.
    Only employees can upload bills.
    """
    start_time = time.time()
    
    try:
        # Validate file type
        allowed_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'pdf']
        file_extension = file.filename.lower().split('.')[-1] if file.filename else ''
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail="File size too large. Maximum size allowed is 10MB."
            )
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded."
            )
        
        logger.info(f"Processing bill for file: {file.filename} (size: {len(file_content)} bytes) for user: {current_user.email}")
        
        # Step 1: Extract text using OCR.Space service
        ocr_success, raw_text, ocr_error = await ocr_space_service.extract_text_from_file(
            file_content, file.filename
        )
        
        if not ocr_success:
            logger.warning(f"OCR failed for {file.filename}: {ocr_error}")
            return BillProcessingResult(
                success=False,
                message=f"OCR extraction failed: {ocr_error}",
                error=ocr_error
            )
        
        if not raw_text or len(raw_text.strip()) < 10:
            return BillProcessingResult(
                success=False,
                message="Insufficient text extracted from the image. Please ensure the image contains clear, readable text.",
                error="Insufficient text extracted"
            )
        
        logger.info(f"OCR successful for {file.filename}. Extracted {len(raw_text)} characters.")
        
        # Step 2: Process extracted text to get structured financial data
        try:
            financial_data, confidence_score, warnings = await bill_processing_service.process_bill_text(
                raw_text, file.filename
            )
            
            processing_time = time.time() - start_time
            
            # Step 3: Ensure user exists in PostgreSQL and get PostgreSQL user ID
            pg_user_id = await ensure_user_in_postgres(current_user.email)
            if not pg_user_id:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to sync user to PostgreSQL database"
                )
            
            # Step 4: Store bill data in PostgreSQL
            # Convert FinancialData.date (string) to a Python date for DB insert
            db_date = None
            try:
                if financial_data.date:
                    if isinstance(financial_data.date, str):
                        db_date = datetime.strptime(financial_data.date, '%Y-%m-%d').date()
                    elif isinstance(financial_data.date, date):
                        db_date = financial_data.date
            except Exception:
                db_date = None

            bill_data = {
                'employee_id': pg_user_id,
                'filename': file.filename,
                'file_type': file_extension,
                'date': db_date,
                'vendor': financial_data.vendor,
                'category': financial_data.category,
                'amount': financial_data.amount,
                'subtotal': financial_data.subtotal,
                'tax': financial_data.tax,
                'discount': financial_data.discount,
                'currency': financial_data.currency,
                'remarks': financial_data.remarks,
                'raw_text': raw_text,
                'confidence_score': confidence_score,
                'processing_time': processing_time,
                'status': 'draft' if submit_mode == 'manual' else 'under_review'
            }
            
            try:
                bill_id = await db_manager.insert_bill(bill_data)
                logger.info(f"Bill stored successfully with ID: {bill_id}")
                
                # Create a simple bill response without fetching from DB to avoid validation issues
                bill_response = BillResponse(
                    id=bill_id,
                    employee_id=pg_user_id,
                    filename=file.filename,
                    file_type=file_extension,
                    vendor=financial_data.vendor,
                    category=financial_data.category,
                    amount=financial_data.amount,
                    subtotal=financial_data.subtotal,
                    tax=financial_data.tax,
                    discount=financial_data.discount,
                    currency=financial_data.currency,
                    remarks=financial_data.remarks,
                    confidence_score=confidence_score,
                    processing_time=processing_time,
                    status='draft' if submit_mode == 'manual' else 'under_review',
                    created_at=datetime.utcnow()
                )
                
                return BillProcessingResult(
                    success=True,
                    bill_id=bill_id,
                    message=f"Bill processed and stored successfully! Confidence: {(confidence_score * 100):.1f}%",
                    bill_data=bill_response
                )
                
            except Exception as db_error:
                logger.error(f"Database insertion failed for {file.filename}: {str(db_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to store bill data in database: {str(db_error)}"
                )
            
        except Exception as processing_error:
            logger.error(f"Bill processing failed for {file.filename}: {str(processing_error)}")
            return BillProcessingResult(
                success=False,
                message=f"Financial data extraction failed: {str(processing_error)}",
                error=str(processing_error)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in process_bill_with_storage: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during bill processing: {str(e)}"
        )

@router.get("/my-bills", response_model=BillListResponse)
async def get_my_bills(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: TokenData = Depends(get_current_employee)
):
    """
    Get bills uploaded by the current employee.
    Only employees can access their own bills.
    """
    try:
        # Get PostgreSQL user ID
        pg_user_id = await ensure_user_in_postgres(current_user.email)
        if not pg_user_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to sync user to PostgreSQL database"
            )
        
        offset = (page - 1) * page_size
        bills = await db_manager.get_bills_by_employee(
            pg_user_id, 
            limit=page_size, 
            offset=offset
        )
        
        # Get total count for pagination
        total_count_result = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM app_bills WHERE employee_id = $1",
            pg_user_id
        )
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
        logger.error(f"Error fetching bills for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch bills: {str(e)}"
        )

@router.get("/team-bills", response_model=BillListResponse)
async def get_team_bills(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Get all bills from employees under the current manager.
    Only managers can access team bills.
    """
    try:
        # Get PostgreSQL user ID for manager
        pg_user_id = await ensure_user_in_postgres(current_user.email)
        if not pg_user_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to sync manager to PostgreSQL database"
            )
        
        offset = (page - 1) * page_size
        bills = await db_manager.get_all_bills_for_manager(
            pg_user_id, 
            limit=page_size, 
            offset=offset
        )
        
        # Get total count for pagination
        total_count_result = await db_manager.execute_query(
            """SELECT COUNT(*) as count FROM app_bills b 
               JOIN app_users u ON b.employee_id = u.id 
               WHERE u.manager_id = $1 OR u.id = $1""",
            pg_user_id
        )
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
        logger.error(f"Error fetching team bills for manager {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch team bills: {str(e)}"
        )

@router.get("/view-bills", response_model=BillListResponse)
async def view_bills(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    View bills based on user role:
    - Employees: only their own bills
    - Managers: all bills from their team
    """
    if current_user.role == "employee":
        return await get_my_bills(page, page_size, current_user)
    elif current_user.role == "manager":
        return await get_team_bills(page, page_size, current_user)
    else:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Invalid user role."
        )

@router.get("/statistics", response_model=BillStatistics)
async def get_bill_statistics(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get bill statistics:
    - Employees: their own statistics
    - Managers: team statistics
    """
    try:
        if current_user.role == "employee":
            stats = await db_manager.get_bill_statistics(int(current_user.user_id))
        elif current_user.role == "manager":
            # Get statistics for all employees under this manager
            stats = await db_manager.execute_query(
                """SELECT 
                    COUNT(*) as total_bills,
                    COALESCE(SUM(amount), 0) as total_amount,
                    COALESCE(AVG(amount), 0) as avg_amount,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_bills,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_bills,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_bills
                FROM bills b
                JOIN users u ON b.employee_id = u.id
                WHERE u.manager_id = $1 OR u.id = $1""",
                int(current_user.user_id)
            )
            stats = stats[0] if stats else {}
        else:
            raise HTTPException(status_code=403, detail="Invalid user role")
        
        return BillStatistics(**stats)
        
    except Exception as e:
        logger.error(f"Error fetching statistics for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch statistics: {str(e)}"
        )

@router.put("/bills/{bill_id}/status")
async def update_bill_status(
    bill_id: int,
    status: str,
    current_user: TokenData = Depends(get_current_manager)
):
    """
    Update bill status (approve/reject).
    Only managers can update bill status.
    """
    valid_statuses = ['pending', 'approved', 'rejected', 'under_review']
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    try:
        # Check if bill exists and belongs to manager's team
        bill_check = await db_manager.execute_query(
            """SELECT b.id FROM bills b
               JOIN users u ON b.employee_id = u.id
               WHERE b.id = $1 AND (u.manager_id = $2 OR u.id = $2)""",
            bill_id, int(current_user.user_id)
        )
        
        if not bill_check:
            raise HTTPException(
                status_code=404,
                detail="Bill not found or access denied"
            )
        
        success = await db_manager.update_bill_status(bill_id, status)
        
        if success:
            return {"message": f"Bill status updated to {status}", "bill_id": bill_id}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update bill status"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bill status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update bill status: {str(e)}"
        )

from pydantic import BaseModel

class SubmitBillRequest(BaseModel):
    remarks: str = ""

@router.put("/{bill_id}/submit-to-manager")
async def submit_bill_to_manager(
    bill_id: int,
    request: SubmitBillRequest,
    current_user: TokenData = Depends(get_current_employee)
):
    """
    Submit a bill to manager for approval.
    Only employees can submit their own bills.
    Changes status from 'draft' to 'under_review'.
    """
    try:
        # Ensure user exists in PostgreSQL
        pg_user_id = await ensure_user_in_postgres(current_user.email)
        if not pg_user_id:
            raise HTTPException(
                status_code=400,
                detail="User not found in system"
            )
        
        # Check if bill exists and belongs to current user
        bill_check = await db_manager.execute_query(
            "SELECT id, status FROM bills WHERE id = $1 AND employee_id = $2",
            bill_id, pg_user_id
        )
        
        if not bill_check:
            raise HTTPException(
                status_code=404,
                detail="Bill not found or access denied"
            )
        
        current_status = bill_check[0]['status']
        
        # Only allow submission of draft bills
        if current_status != 'draft':
            raise HTTPException(
                status_code=400,
                detail=f"Cannot submit bill with status '{current_status}'. Only draft bills can be submitted."
            )
        
        # Update bill status to under_review and add remarks
        update_query = """
            UPDATE app_bills 
            SET status = 'under_review', 
                remarks = COALESCE(NULLIF($2, ''), remarks),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        
        await db_manager.execute_query(update_query, bill_id, request.remarks)
        
        logger.info(f"✅ Employee {current_user.email} submitted bill {bill_id} to manager")
        
        return {
            "message": "Bill submitted to manager successfully",
            "bill_id": bill_id,
            "status": "under_review"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting bill to manager: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit bill to manager: {str(e)}"
        )

@router.get("/health")
async def postgres_bill_processing_health_check(current_user: TokenData = Depends(get_current_user)):
    """Health check endpoint for PostgreSQL bill processing service"""
    try:
        # Test database connection
        await db_manager.execute_query("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "Bill Processing with PostgreSQL",
            "user": current_user.email,
            "role": current_user.role,
            "database": "connected",
            "features": [
                "OCR text extraction",
                "Financial data parsing",
                "PostgreSQL storage",
                "Role-based access control",
                "Bill status management",
                "Statistics and reporting"
            ],
            "supported_formats": ["jpg", "jpeg", "png", "bmp", "tiff", "gif", "pdf"],
            "supported_categories": [
                "food", "transport", "lodging", "fuel", "entertainment", 
                "office_supplies", "communication", "medical", "miscellaneous"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Bill Processing with PostgreSQL",
            "error": str(e),
            "database": "disconnected"
        }