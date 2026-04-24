from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from models.user_models import TokenData
from dependencies.auth_dependencies import get_current_user, get_current_employee
from services.enhanced_bill_processor import enhanced_bill_processor
from database import db_manager
import logging
from datetime import datetime, date
from typing import Dict, Any, List
import time
import hashlib

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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bills", tags=["Enhanced Bill Processing"])

# Also add a primary upload endpoint without prefix for easier access
upload_router = APIRouter(tags=["Primary Bill Upload"])

async def ensure_user_in_postgres(user_email: str) -> int:
    """Ensure user exists in PostgreSQL, sync from MongoDB if needed"""
    try:
        # Check if user exists in PostgreSQL
        pg_user = await db_manager.get_user_by_email(user_email)
        if pg_user:
            return pg_user['id']
        
        # Get user from MongoDB
        if users_collection is None:
            logger.error("MongoDB users collection not available")
            raise HTTPException(status_code=500, detail="Database connection error")
            
        mongo_user = users_collection.find_one({"email": user_email})
        if not mongo_user:
            logger.error(f"User {user_email} not found in MongoDB")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Sync user to PostgreSQL
        user_id = await db_manager.sync_user_from_mongodb(mongo_user)
        logger.info(f"Synced user {user_email} to PostgreSQL with ID {user_id}")
        return user_id
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ensuring user in PostgreSQL: {e}")
        raise HTTPException(status_code=500, detail="Database synchronization error")

@router.post("/process-enhanced")
async def process_enhanced_bill(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_employee)
) -> Dict[str, Any]:
    """
    Enhanced bill processing using OCR.Space + Gemini 2.0 Flash + Regex fallback.
    Returns structured bill data with high accuracy.
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
            
        # Duplicate detection using hashing
        file_hash = hashlib.sha256(file_content).hexdigest()
        existing_bill = await db_manager.get_bill_by_hash(file_hash)
        if existing_bill:
            logger.warning(f"Duplicate bill detected: {file.filename} matches hash {file_hash}")
            raise HTTPException(
                status_code=400,
                detail="Duplicate bill detected. This exact image/file has already been uploaded."
            )
        
        logger.info(f"Processing enhanced bill: {file.filename} (size: {len(file_content)} bytes) for user: {current_user.email}")
        
        # Process the bill using enhanced pipeline
        success, bill_data, error_message = await enhanced_bill_processor.process_bill(
            file_content, file.filename
        )
        
        if not success:
            logger.error(f"Enhanced bill processing failed for {file.filename}: {error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"Bill processing failed: {error_message}"
            )
        
        # Ensure user exists in PostgreSQL
        pg_user_id = await ensure_user_in_postgres(current_user.email)
        
        # Prepare data for database storage
        db_date = None
        if bill_data.get("date"):
            try:
                db_date = datetime.strptime(bill_data["date"], '%Y-%m-%d').date()
            except Exception as e:
                logger.warning(f"Could not parse date: {bill_data['date']} - {e}")
                db_date = None
        
        # Map category for database storage
        category_mapping = {
            "food": "food",
            "travel": "transport", 
            "rent": "lodging",
            "miscellaneous": "miscellaneous"
        }
        
        # Check for active trip and get trip ID
        active_trip_id = None
        trip_status = 'individual'  # Default for non-trip bills
        
        try:
            from services.trip_budget_service import trip_budget_service
            active_session = trip_budget_service.get_active_trip_session(current_user.user_id)
            if active_session:
                active_trip_id = active_session.trip_id
                trip_status = 'trip_expense'
                logger.info(f"Bill {file.filename} associated with active trip {active_trip_id}")
        except Exception as e:
            logger.warning(f"Could not check for active trip: {e}")

        # Apply Rule Engine & Fraud Detection (Confidence Score Logic)
        confidence = float(bill_data.get("confidence_score") if bill_data.get("confidence_score") is not None else 0.8)
        amount_val = bill_data.get("amount")
        amount = float(amount_val) if amount_val is not None else 0.0
        
        initial_status = 'pending'
        rejection_reason = None
        
        # Fraud detection rules
        if amount > 10000:
            # Abnormal amount
            initial_status = 'rejected'
            rejection_reason = "Flagged: Abnormal amount exceeding maximum policy limit."
        elif not bill_data.get("amount") or not bill_data.get("vendor"):
            initial_status = 'rejected'
            rejection_reason = "Flagged: Missing mandatory fields (Amount or Vendor)."
        else:
            # Confidence score rules
            if confidence >= 0.8:
                initial_status = 'approved'
            elif confidence >= 0.6:
                initial_status = 'pending'  # Send to manager
            else:
                initial_status = 'under_review'
                rejection_reason = f"Flagged: AI confidence score too low ({confidence*100:.1f}%). Manager review required."

        # Prepare database record
        db_bill_data = {
            'employee_id': pg_user_id,
            'trip_id': active_trip_id,
            'filename': file.filename,
            'file_type': file_extension,
            'file_hash': file_hash,
            'date': db_date,
            'vendor': bill_data.get("vendor"),
            'category': category_mapping.get(bill_data.get("category", "miscellaneous"), "miscellaneous"),
            'amount': bill_data.get("amount"),
            'subtotal': bill_data.get("subtotal"),
            'tax': bill_data.get("tax"),
            'discount': bill_data.get("discount"),
            'currency': bill_data.get("currency", "INR"),
            'remarks': f"Processed via {bill_data.get('parsing_method', 'enhanced')} pipeline. " +
                      f"Payment: {bill_data.get('payment_method', 'unknown')}. " +
                      f"Invoice: {bill_data.get('invoice_number', 'N/A')}",
            'raw_text': bill_data.get("raw_text", ""),
            'confidence_score': confidence,
            'processing_time': bill_data.get("processing_time", time.time() - start_time),
            'status': initial_status,
            'rejection_reason': rejection_reason,
            'trip_status': trip_status
        }
        
        # Validate against active trip budget
        trip_validation = None
        try:
            from services.trip_budget_service import trip_budget_service
            from models.budget_models import ExpenseType
            from decimal import Decimal
            
            if bill_data.get("amount"):
                # Map category to expense type
                expense_type_mapping = {
                    "food": ExpenseType.FOOD,
                    "travel": ExpenseType.TRAVEL,
                    "transport": ExpenseType.LOCAL_TRANSPORT,
                    "lodging": ExpenseType.HOTEL,
                    "rent": ExpenseType.HOTEL,
                    "miscellaneous": ExpenseType.MISCELLANEOUS
                }
                
                category = bill_data.get("category", "miscellaneous")
                expense_type = expense_type_mapping.get(category, ExpenseType.MISCELLANEOUS)
                amount = Decimal(str(bill_data.get("amount", 0)))
                
                # Validate expense against active trip
                trip_validation = trip_budget_service.validate_trip_expense(
                    employee_id=current_user.user_id,
                    expense_type=expense_type,
                    amount=amount
                )
                
                # Record expense if within budget
                if trip_validation.is_within_budget:
                    trip_budget_service.record_trip_expense(
                        employee_id=current_user.user_id,
                        expense_type=expense_type,
                        amount=amount
                    )
                
                logger.info(f"Trip budget validation for bill {file.filename}: within_budget={trip_validation.is_within_budget}")
                
        except Exception as budget_error:
            logger.warning(f"Trip budget validation failed for {file.filename}: {budget_error}")
            # Continue processing even if budget validation fails

        # Store in database
        try:
            bill_id = await db_manager.insert_bill_with_trip(db_bill_data)
            logger.info(f"Enhanced bill stored successfully with ID: {bill_id} (Trip: {active_trip_id or 'None'})")
            
            # Prepare trip budget validation message
            budget_message = ""
            if trip_validation:
                if trip_validation.is_within_budget:
                    budget_message = f" ✅ Within trip budget (₹{trip_validation.remaining_budget:.2f} remaining for {trip_validation.expense_type.value})."
                else:
                    budget_message = f" ⚠️ {trip_validation.warning_message}"
            
            # Prepare response
            response_data = {
                "success": True,
                "bill_id": bill_id,
                "message": f"Bill processed successfully using {bill_data.get('parsing_method', 'enhanced')} method!{budget_message}",
                "bill_data": {
                    "id": bill_id,
                    "employee_id": pg_user_id,
                    "employee_name": current_user.username or current_user.email,
                    "filename": file.filename,
                    "date": bill_data.get("date"),
                    "vendor": bill_data.get("vendor"),
                    "category": bill_data.get("category"),
                    "amount": bill_data.get("amount"),
                    "subtotal": bill_data.get("subtotal"),
                    "tax": bill_data.get("tax"),
                    "discount": bill_data.get("discount"),
                    "currency": bill_data.get("currency"),
                    "payment_method": bill_data.get("payment_method"),
                    "invoice_number": bill_data.get("invoice_number"),
                    "description": bill_data.get("description"),
                    "travel_from": bill_data.get("travel_from"),
                    "travel_to": bill_data.get("travel_to"),
                    "confidence_score": bill_data.get("confidence_score"),
                    "processing_time": bill_data.get("processing_time"),
                    "parsing_method": bill_data.get("parsing_method"),
                    "status": initial_status,
                    "rejection_reason": rejection_reason
                },
                "processing_info": {
                    "parsing_method": bill_data.get("parsing_method"),
                    "confidence_score": bill_data.get("confidence_score"),
                    "processing_time": bill_data.get("processing_time"),
                    "validation_warnings": bill_data.get("validation_warnings", [])
                },
                "trip_budget_validation": {
                    "is_within_budget": trip_validation.is_within_budget if trip_validation else None,
                    "trip_id": trip_validation.trip_id if trip_validation else None,
                    "allocated_budget": float(trip_validation.allocated_budget) if trip_validation else None,
                    "used_budget": float(trip_validation.used_budget) if trip_validation else None,
                    "remaining_budget": float(trip_validation.remaining_budget) if trip_validation else None,
                    "warning_message": trip_validation.warning_message if trip_validation else None,
                    "recommendation": trip_validation.recommendation if trip_validation else None
                } if trip_validation else None
            }
            
            return response_data
            
        except Exception as db_error:
            logger.error(f"Database insertion failed for {file.filename}: {str(db_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store bill data in database: {str(db_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in enhanced bill processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during bill processing: {str(e)}"
        )

@router.get("/my-bills-enhanced")
async def get_my_bills_enhanced(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: TokenData = Depends(get_current_employee)
) -> Dict[str, Any]:
    """Get employee's bills with enhanced processing information"""
    try:
        # Ensure user exists in PostgreSQL
        pg_user_id = await ensure_user_in_postgres(current_user.email)
        
        # Get bills from database
        bills = await db_manager.get_bills_by_employee(pg_user_id, limit, offset)
        
        # Get statistics
        stats = await db_manager.get_bill_statistics(pg_user_id)
        
        return {
            "success": True,
            "bills": bills,
            "statistics": stats,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total_bills": stats.get("total_bills", 0)
            },
            "user_info": {
                "employee_id": pg_user_id,
                "email": current_user.email,
                "username": current_user.username
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching enhanced bills for {current_user.email}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch bills: {str(e)}"
        )

def _safe_date_str(value):
    """Safely convert a date value to ISO string. Handles both Python date objects and strings from SQLite."""
    if value is None:
        return None
    if isinstance(value, str):
        return value  # SQLite already returns strings
    try:
        return value.isoformat()
    except Exception:
        return str(value)

@router.get("/my-bills")
async def get_my_bills(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get employee's bills - simplified endpoint for frontend"""
    try:
        # Ensure user exists in PostgreSQL
        pg_user_id = await ensure_user_in_postgres(current_user.email)
        
        # Get bills from database
        bills = await db_manager.get_bills_by_employee(pg_user_id, limit, offset)
        
        # Format bills for frontend
        formatted_bills = []
        for bill in bills:
            formatted_bills.append({
                "id": bill['id'],
                "filename": bill.get('filename'),
                "date": _safe_date_str(bill.get('date')),
                "vendor": bill.get('vendor'),
                "category": bill.get('category'),
                "amount": float(bill['amount']) if bill.get('amount') else 0,
                "subtotal": float(bill['subtotal']) if bill.get('subtotal') else None,
                "tax": float(bill['tax']) if bill.get('tax') else None,
                "currency": bill.get('currency'),
                "status": bill.get('status', 'pending'),
                "trip_status": bill.get('trip_status', 'individual'),
                "trip_id": bill.get('trip_id'),
                "confidence_score": float(bill['confidence_score']) if bill.get('confidence_score') else None,
                "remarks": bill.get('remarks'),
                "rejection_reason": bill.get('rejection_reason'),
                "justification": bill.get('justification'),
                "created_at": _safe_date_str(bill.get('created_at')),
                "updated_at": _safe_date_str(bill.get('updated_at'))
            })
        
        # Get statistics for dashboard
        stats = await db_manager.get_bill_statistics(pg_user_id)
        
        return {
            "success": True,
            "bills": formatted_bills,
            "total_count": len(formatted_bills),
            "statistics": stats,
            "user_info": {
                "employee_id": pg_user_id,
                "email": current_user.email,
                "username": current_user.username
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching bills for {current_user.email}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch bills: {str(e)}"
        )

@router.get("/processing-status")
async def get_processing_status():
    """Get status of all processing services"""
    try:
        status = enhanced_bill_processor.get_service_status()
        
        # Add overall health check
        all_services_available = all(
            service['available'] for service in status.values() 
            if isinstance(service, dict) and 'available' in service
        )
        
        return {
            "success": True,
            "overall_status": "healthy" if all_services_available else "degraded",
            "services": status,
            "message": "All services operational" if all_services_available else "Some services unavailable"
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        return {
            "success": False,
            "error": str(e),
            "overall_status": "error"
        }

@router.post("/reprocess-bill/{bill_id}")
async def reprocess_bill(
    bill_id: int,
    current_user: TokenData = Depends(get_current_employee)
) -> Dict[str, Any]:
    """Reprocess an existing bill with enhanced pipeline"""
    try:
        # Ensure user exists in PostgreSQL
        pg_user_id = await ensure_user_in_postgres(current_user.email)
        
        # Get the bill from database
        bills = await db_manager.get_bills_by_employee(pg_user_id, limit=1, offset=0)
        bill = next((b for b in bills if b['id'] == bill_id), None)
        
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        # Check if we have raw text to reprocess
        raw_text = bill.get('raw_text')
        if not raw_text:
            raise HTTPException(
                status_code=400, 
                detail="Cannot reprocess bill: no raw OCR text available"
            )
        
        # Reprocess using Gemini + Regex (skip OCR since we have text)
        logger.info(f"Reprocessing bill {bill_id} for user {current_user.email}")
        
        # Try Gemini parsing
        bill_data = None
        parsing_method = "reprocess_unknown"
        
        if enhanced_bill_processor.ai_parser.is_available():
            gemini_data, gemini_error = await enhanced_bill_processor.ai_parser.analyze_bill_async(
                raw_text, bill.get('filename', 'unknown')
            )
            
            if gemini_data and gemini_error is None:
                bill_data = gemini_data
                parsing_method = "reprocess_gemini"
        
        # Fallback to regex if needed
        if not bill_data or bill_data.get('confidence_score', 0) < 0.6:
            regex_data = enhanced_bill_processor.fallback_parser.parse_bill_data(
                raw_text, bill.get('filename', 'unknown')
            )
            
            if bill_data:
                bill_data = enhanced_bill_processor._merge_bill_data(bill_data, regex_data)
                parsing_method = "reprocess_hybrid"
            else:
                bill_data = regex_data
                parsing_method = "reprocess_regex"
        
        if not bill_data:
            raise HTTPException(status_code=400, detail="Reprocessing failed")
        
        # Update the bill in database
        db_date = None
        if bill_data.get("date"):
            try:
                db_date = datetime.strptime(bill_data["date"], '%Y-%m-%d').date()
            except Exception:
                db_date = bill.get('date')  # Keep original date if parsing fails
        
        # Update bill data
        update_query = """
        UPDATE app_bills SET 
            date = $1, vendor = $2, amount = $3, subtotal = $4, tax = $5, 
            discount = $6, currency = $7, confidence_score = $8, 
            remarks = $9, updated_at = CURRENT_TIMESTAMP
        WHERE id = $10 AND employee_id = $11
        """
        
        await db_manager.execute_command(
            update_query,
            db_date,
            bill_data.get("vendor"),
            bill_data.get("amount"),
            bill_data.get("subtotal"),
            bill_data.get("tax"),
            bill_data.get("discount"),
            bill_data.get("currency", "INR"),
            bill_data.get("confidence_score", 0.8),
            f"Reprocessed via {parsing_method}. Payment: {bill_data.get('payment_method', 'unknown')}",
            bill_id,
            pg_user_id
        )
        
        return {
            "success": True,
            "message": f"Bill reprocessed successfully using {parsing_method}",
            "bill_id": bill_id,
            "updated_data": bill_data,
            "parsing_method": parsing_method
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing bill {bill_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reprocess bill: {str(e)}"
        )

@router.post("/bill/{bill_id}/justify")
async def submit_justification(
    bill_id: int,
    justification: str = Query(...),
    current_user: TokenData = Depends(get_current_employee)
) -> Dict[str, Any]:
    """Submit justification for a flagged/rejected bill and analyze it"""
    try:
        pg_user_id = await ensure_user_in_postgres(current_user.email)
        bills = await db_manager.get_bills_by_employee(pg_user_id, limit=100)
        bill = next((b for b in bills if b['id'] == bill_id), None)
        
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
            
        if bill['status'] not in ['rejected', 'pending']:
            raise HTTPException(status_code=400, detail="Can only justify flagged or rejected bills.")
            
        # Simple NLP logic for justification analysis
        # If justification is longer than 20 characters and contains keywords, set to pending for manager review
        just_lower = justification.lower()
        valid_keywords = ['mistake', 'sorry', 'urgent', 'approved by', 'client', 'emergency', 'exception']
        
        is_valid = len(just_lower) > 20 and any(kw in just_lower for kw in valid_keywords)
        
        # If valid, we move it to under_review so manager can see it
        await db_manager.update_bill_justification(bill_id, justification)
        
        return {
            "success": True,
            "message": "Justification submitted successfully and is under manager review.",
            "is_valid_analysis": is_valid
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting justification for bill {bill_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit justification")

@router.get("/bill/{bill_id}/report", response_class=HTMLResponse)
async def generate_bill_report(
    bill_id: int,
    current_user: TokenData = Depends(get_current_employee)
):
    """Generate a printable HTML report for a bill"""
    try:
        pg_user_id = await ensure_user_in_postgres(current_user.email)
        bills = await db_manager.get_bills_by_employee(pg_user_id, limit=100)
        bill = next((b for b in bills if b['id'] == bill_id), None)
        
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
            
        html_content = f"""
        <html>
            <head>
                <title>Expense Claim Report - #{bill['id']}</title>
                <style>
                    body {{ font-family: 'Inter', sans-serif; padding: 40px; color: #333; }}
                    .header {{ border-bottom: 2px solid #28a745; padding-bottom: 20px; margin-bottom: 20px; }}
                    .title {{ font-size: 24px; font-weight: bold; color: #28a745; }}
                    .details {{ margin-bottom: 30px; }}
                    .row {{ display: flex; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                    .label {{ font-weight: bold; width: 200px; }}
                    .value {{ flex: 1; }}
                    .status {{ padding: 5px 10px; border-radius: 4px; font-weight: bold; color: white; display: inline-block; }}
                    .status.approved {{ background: #28a745; }}
                    .status.rejected {{ background: #dc3545; }}
                    .status.pending {{ background: #ffc107; color: #333; }}
                    .status.under_review {{ background: #17a2b8; }}
                    .footer {{ margin-top: 50px; font-size: 12px; color: #777; text-align: center; }}
                    @media print {{
                        button {{ display: none; }}
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="title">Xpensify Claim Report</div>
                    <div>Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                
                <button onclick="window.print()" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 20px;">Download PDF / Print</button>
                
                <div class="details">
                    <h3>Claim Details</h3>
                    <div class="row"><div class="label">Bill ID:</div><div class="value">#{bill['id']}</div></div>
                    <div class="row"><div class="label">Employee:</div><div class="value">{current_user.full_name or current_user.username} ({current_user.email})</div></div>
                    <div class="row"><div class="label">Vendor:</div><div class="value">{bill.get('vendor', 'N/A')}</div></div>
                    <div class="row"><div class="label">Date:</div><div class="value">{bill.get('date', 'N/A')}</div></div>
                    <div class="row"><div class="label">Category:</div><div class="value">{bill.get('category', 'N/A')}</div></div>
                    <div class="row"><div class="label">Amount:</div><div class="value">{bill.get('currency', 'USD')} {bill.get('amount', '0.00')}</div></div>
                    <div class="row"><div class="label">Status:</div><div class="value"><span class="status {bill.get('status', 'pending')}">{bill.get('status', 'PENDING').upper()}</span></div></div>
                </div>
                
                <div class="details">
                    <h3>AI Verification</h3>
                    <div class="row"><div class="label">Confidence Score:</div><div class="value">{float(bill.get('confidence_score', 0))*100:.1f}%</div></div>
                    <div class="row"><div class="label">AI Remarks:</div><div class="value">{bill.get('remarks', 'N/A')}</div></div>
                    <div class="row"><div class="label">Rejection Reason:</div><div class="value">{bill.get('rejection_reason', 'N/A')}</div></div>
                    <div class="row"><div class="label">User Justification:</div><div class="value">{bill.get('justification', 'N/A')}</div></div>
                </div>
                
                <div class="footer">
                    Xpensify Expense Management System &copy; 2026. This is an automatically generated report.
                </div>
            </body>
        </html>
        """
        return html_content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report for bill {bill_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

# Primary upload endpoint (without /bills prefix for easier frontend access)
@upload_router.post("/upload")
async def upload_bill_primary(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_employee)
) -> Dict[str, Any]:
    """
    Primary bill upload endpoint - uses enhanced processing pipeline
    This is the main endpoint for bill uploads in the application
    """
    return await process_enhanced_bill(file, current_user)