from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"

class RegisterUser(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = Field(default=UserRole.EMPLOYEE, description="User role: employee or manager")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name of the user")
    department: Optional[str] = Field(None, max_length=50, description="Department/Team")
    manager_id: Optional[str] = Field(None, description="Manager's user ID (for employees)")
    designation: Optional[str] = Field(None, max_length=50, description="Employee designation (Intern, Associate, Manager, etc.)")
    work_city: Optional[str] = Field(None, max_length=50, description="Primary work city")
    employee_id: Optional[str] = Field(None, max_length=20, description="Company employee ID")

class LoginUser(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[str] = None
    designation: Optional[str] = None
    work_city: Optional[str] = None
    employee_id: Optional[str] = None
    created_at: Optional[str] = None

class TokenData(BaseModel):
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    role: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[str] = None
    designation: Optional[str] = None
    work_city: Optional[str] = None
    employee_id: Optional[str] = None

class JWTToken(BaseModel):
    access_token: str
    token_type: str
    user_data: TokenData
    expires_in: int