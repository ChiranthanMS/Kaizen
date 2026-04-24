from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from typing import Optional, Dict
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pathlib import Path
import secrets
import re
import random
import smtplib
import ssl
from email.mime.text import MIMEText
import sendgrid
from sendgrid.helpers.mail import Mail
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# Load environment variables from backend/.env and project root /.env
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
# Load backend .env first (lower priority)
load_dotenv(backend_dir / ".env")
# Then load project root .env to override
load_dotenv(project_root / ".env", override=True)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# SMTP config (optional)
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "no-reply@example.com")

# SendGrid config
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM = os.getenv("SENDGRID_FROM", "no-reply@example.com")

# JWT Settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize MongoDB service for user authentication
from services.mongodb_service import mongodb_service

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme is defined in auth_dependencies.py

# Database startup and shutdown events
from database import startup_database, shutdown_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_database()
    yield
    # Shutdown
    await shutdown_database()

app = FastAPI(
    title="Enhanced Travel Expense Management API", 
    description="A comprehensive API for managing travel expenses with enhanced OCR bill processing",
    version="2.0.0",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Enhanced Travel Expense Management API is running",
        "version": "2.0.0",
        "features": [
            "OCR.Space text extraction",
            "Gemini 2.0 Flash AI parsing",
            "Regex fallback parser",
            "Enhanced bill processing pipeline"
        ]
    }

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Primary Enhanced Bill Processing routes (OCR.Space + Gemini 2.0 Flash + Regex fallback)
try:
    from routes.enhanced_bill_routes import router as enhanced_bill_router, upload_router
    app.include_router(enhanced_bill_router)
    app.include_router(upload_router)
    print("Enhanced bill processing routes loaded (OCR.Space + Gemini 2.0 Flash + Regex)")
    print("Primary upload endpoint available at /upload")
except ImportError as e:
    print(f"Error: Could not import enhanced bill routes: {e}")
    print("Enhanced bill processing will not be available.")

# Legacy routes removed - Enhanced processing handles all bill operations

# Include Manager routes
try:
    from routes.manager_routes import router as manager_router
    app.include_router(manager_router)
    print("Manager functionality loaded")
except ImportError as e:
    print(f"Warning: Could not import manager routes: {e}")
    print("Manager functionality will not be available.")

# Include Analytics routes
try:
    from routes.analytics_routes import router as analytics_router
    app.include_router(analytics_router)
    print("Analytics functionality loaded")
except ImportError as e:
    print(f"Warning: Could not import analytics routes: {e}")
    print("Analytics functionality will not be available.")

# Include OCR Health Monitoring routes
try:
    from routes.ocr_health_routes import router as ocr_health_router
    app.include_router(ocr_health_router)
    print("OCR health monitoring loaded")
except ImportError as e:
    print(f"Warning: Could not import OCR health routes: {e}")
    print("OCR health monitoring will not be available.")

# Include Trip Budget Management routes
try:
    from routes.trip_budget_routes import router as trip_budget_router
    app.include_router(trip_budget_router)
    print("Trip-based budget management system loaded")
except ImportError as e:
    print(f"Warning: Could not import trip budget routes: {e}")
    print("Trip budget management will not be available.")

# Import models from separate file
from models.user_models import RegisterUser, LoginUser, UserResponse, JWTToken, UserRole
from services.auth_service import auth_service

# Keep existing models for backward compatibility

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class GoogleUser(BaseModel):
    email: str
    name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    message: str

class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    auth_type: Optional[str] = None

class UserInDB(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    auth_type: str

@app.get("/")
async def root():
    return {"message": "Authentication API is running", "status": "healthy"}

# Helpers to abstract storage using MongoDB service
def find_user_by_username(username: str) -> Optional[Dict]:
    return mongodb_service.find_user_by_username(username)

def find_user_by_email(email: str) -> Optional[Dict]:
    return mongodb_service.find_user_by_email(email)

# Google specific
def find_google_user_by_email(email: str) -> Optional[Dict]:
    user = mongodb_service.find_user_by_email(email)
    if user and user.get("auth_type") == "google":
        return user
    return None

def insert_user(user_doc: Dict):
    return mongodb_service.create_user(user_doc)

# Password policy: min 8 chars, upper, lower, digit, special
def validate_password_strength(password: str):
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("an uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("a lowercase letter")
    if not re.search(r"\d", password):
        errors.append("a number")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("a special character")
    if errors:
        raise HTTPException(status_code=400, detail=f"Password must contain {', '.join(errors)}")

# Email sending

def send_reset_code_email(to_email: str, code: str):
    subject = "Your password reset code"
    body = f"Your password reset code is: {code}\nThis code will expire in 10 minutes."
    if not SENDGRID_API_KEY:
        print(f"[DEV] Password reset code for {to_email}: {code}")
        return
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        message = Mail(
            from_email=SENDGRID_FROM,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )
        response = sg.send(message)
        if response.status_code >= 400:
            print(f"SendGrid error: {response.status_code} {response.body}")
    except Exception as e:
        print(f"SendGrid exception: {e}")

# Password reset storage helpers

def store_reset_code(email: str, code_hash: str, expires_at: datetime):
    mongodb_service.store_password_reset_code(email, code_hash, expires_at)

def fetch_reset_record(email: str) -> Optional[Dict]:
    return mongodb_service.get_password_reset_record(email)

def delete_reset_record(email: str):
    mongodb_service.delete_password_reset_record(email)

@app.post("/register", response_model=Token)
async def register(user: RegisterUser):
    # Validate input
    if not user.username or not user.password or not user.email:
        raise HTTPException(status_code=400, detail="Username, email and password are required")
    if len(user.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
    validate_password_strength(user.password)

    if find_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    if find_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        user_doc = {
            "username": user.username,
            "email": user.email,
            "password": user.password,  # MongoDB service will hash this
            "role": user.role.value,
            "full_name": user.full_name,
            "department": user.department,
            "manager_id": user.manager_id,
            "designation": user.designation,
            "work_city": user.work_city,
            "employee_id": user.employee_id,
            "auth_type": "regular",
            "created_at": datetime.utcnow(),
        }
        insert_user(user_doc)
        
        role_message = "manager" if user.role == UserRole.MANAGER else "employee"
        return {
            "access_token": "",
            "token_type": "bearer",
            "message": f"User registered successfully as {role_message}! Please login with your credentials.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/login", response_model=Token)
async def login(user: LoginUser):
    if not user.password or (not user.username and not user.email):
        raise HTTPException(status_code=400, detail="Provide username or email and password")

    try:
        # Authenticate user using MongoDB service
        email = user.email if user.email else None
        if user.username and not email:
            # Find email by username
            user_by_username = mongodb_service.find_user_by_username(user.username)
            if user_by_username:
                email = user_by_username.get("email")
        
        if not email:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        # Authenticate with MongoDB
        authenticated_user = mongodb_service.authenticate_user(email, user.password)
        if not authenticated_user:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        # Sync user to PostgreSQL for bill storage (if not already synced)
        from database import db_manager
        try:
            await db_manager.sync_user_from_mongodb(authenticated_user)
        except Exception as e:
            logger.warning(f"Could not sync user to PostgreSQL: {e}")
            # Continue with login even if PostgreSQL sync fails

        # Note: Budget allocation now happens only during approved company trips
        # No automatic budget caps are created during login

        # Create access token with role information
        user_data = {
            "user_id": str(authenticated_user.get("_id")),
            "username": authenticated_user.get("username"),
            "email": authenticated_user.get("email"),
            "role": authenticated_user.get("role", "employee"),
            "full_name": authenticated_user.get("full_name"),
            "department": authenticated_user.get("department"),
            "manager_id": authenticated_user.get("manager_id"),
            "designation": authenticated_user.get("designation"),
            "work_city": authenticated_user.get("work_city"),
            "employee_id": authenticated_user.get("employee_id"),
            "auth_type": "regular"
        }
        
        access_token = auth_service.create_access_token(user_data)
        
        role_message = "Manager" if authenticated_user.get("role") == "manager" else "Employee"
        designation_info = f" ({authenticated_user.get('designation', 'Associate')})" if authenticated_user.get("designation") else ""
        city_info = f" from {authenticated_user.get('work_city')}" if authenticated_user.get("work_city") else ""
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "message": f"Welcome, {role_message}{designation_info} {authenticated_user.get('full_name') or authenticated_user.get('username')}{city_info}!",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    # Always respond generically to avoid user enumeration, but only store/send when user exists
    user = find_user_by_email(req.email)
    # Generate 6-digit code
    code = f"{random.randint(0, 999999):06d}"
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    if user:
        code_hash = pwd_context.hash(code)
        store_reset_code(req.email, code_hash, expires_at)
        try:
            send_reset_code_email(req.email, code)
        except Exception as e:
            # Do not reveal errors to client; log only
            print(f"Error sending reset email: {e}")
    return {"message": "If an account with that email exists, a reset code has been sent."}

@app.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    validate_password_strength(req.new_password)
    record = fetch_reset_record(req.email)
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    if record.get("expires_at") < datetime.utcnow():
        delete_reset_record(req.email)
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    if not pwd_context.verify(req.code, record.get("code_hash", "")):
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    # Update user password
    user = find_user_by_email(req.email)
    if not user:
        # Clean up and generic message
        delete_reset_record(req.email)
        return {"message": "Password has been reset if the account exists."}

    new_hash = pwd_context.hash(req.new_password)
    if users_collection is not None:
        users_collection.update_one({"email": req.email}, {"$set": {"password": new_hash}})
    else:
        # Update in-memory user
        if user.get("username"):
            in_memory_users[user["username"]]["password"] = new_hash
        else:
            # google users won't have password; ignore
            pass
    delete_reset_record(req.email)
    return {"message": "Password has been reset successfully. You may now log in."}

@app.post("/google-login", response_model=Token)
async def google_login(user: GoogleUser):
    if not user.email or not user.name:
        raise HTTPException(status_code=400, detail="Email and name are required")

    try:
        existing_user = find_google_user_by_email(user.email)
        
        # Create user data for token
        user_data = {
            "user_id": str(existing_user.get("_id", f"google:{user.email}")) if existing_user else f"google:{user.email}",
            "username": existing_user.get("username") if existing_user else None,
            "email": user.email,
            "role": existing_user.get("role", "employee") if existing_user else "employee",
            "full_name": user.name,
            "department": existing_user.get("department") if existing_user else None,
            "manager_id": existing_user.get("manager_id") if existing_user else None,
            "auth_type": "google"
        }
        
        access_token = auth_service.create_access_token(user_data)

        if existing_user:
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "message": f"Welcome back, {user.name}!",
            }
        else:
            insert_user({
                "email": user.email,
                "name": user.name,
                "auth_type": "google",
                "created_at": datetime.utcnow(),
            })
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "message": f"Google account registered successfully. Welcome, {user.name}!",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google login failed: {str(e)}")

@app.get("/google-client-id")
async def get_google_client_id():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")
    return {"client_id": GOOGLE_CLIENT_ID}

# Use auth service for JWT operations
from dependencies.auth_dependencies import oauth2_scheme, get_current_user

async def get_current_user_legacy(token: str = Depends(oauth2_scheme)):
    """Legacy get_current_user for backward compatibility"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Accept both 'username' (our tokens) and legacy 'sub'
        username = payload.get("username") or payload.get("sub")
        email = payload.get("email")
        auth_type = payload.get("auth_type")
        if (username is None and email is None) or auth_type is None:
            raise credentials_exception
        token_data = TokenData(username=username, email=email, auth_type=auth_type)
    except JWTError:
        raise credentials_exception

    # Lookup user from whichever store is active
    if token_data.auth_type == "regular":
        if token_data.username:
            user = find_user_by_username(token_data.username)
        elif token_data.email:
            user = find_user_by_email(token_data.email)
        else:
            user = None
    elif token_data.auth_type == "google" and token_data.email:
        user = find_google_user_by_email(token_data.email)
    else:
        user = None

    if user is None:
        raise credentials_exception
    return dict(user)

@app.get("/profile")
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    try:
        # Return user data from token
        profile_data = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "full_name": current_user.full_name,
            "department": current_user.department,
            "manager_id": current_user.manager_id
        }
        return profile_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile fetch failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
