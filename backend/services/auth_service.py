from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from models.user_models import UserRole, TokenData
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def create_access_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with user data and role"""
        to_encode = user_data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access_token"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> TokenData:
        """Verify JWT token and extract user data"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Extract user data from token
            user_id: str = payload.get("user_id")
            username: str = payload.get("username")
            email: str = payload.get("email")
            role: str = payload.get("role")
            
            if user_id is None or email is None or role is None:
                raise credentials_exception
            
            # Validate role
            if role not in [UserRole.EMPLOYEE.value, UserRole.MANAGER.value]:
                raise credentials_exception
            
            token_data = TokenData(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                full_name=payload.get("full_name"),
                department=payload.get("department"),
                manager_id=payload.get("manager_id"),
                designation=payload.get("designation"),
                work_city=payload.get("work_city"),
                employee_id=payload.get("employee_id")
            )
            
            return token_data
            
        except JWTError:
            raise credentials_exception

    def require_role(self, token_data: TokenData, required_roles: list) -> bool:
        """Check if user has required role"""
        if token_data.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        return True

    def is_manager(self, token_data: TokenData) -> bool:
        """Check if user is a manager"""
        return token_data.role == UserRole.MANAGER.value

    def is_employee(self, token_data: TokenData) -> bool:
        """Check if user is an employee"""
        return token_data.role == UserRole.EMPLOYEE.value

    def can_access_employee_data(self, token_data: TokenData, employee_id: str) -> bool:
        """Check if user can access specific employee's data"""
        # Managers can access all employee data
        if self.is_manager(token_data):
            return True
        
        # Employees can only access their own data
        if self.is_employee(token_data) and token_data.user_id == employee_id:
            return True
        
        return False

# Global auth service instance
auth_service = AuthService()