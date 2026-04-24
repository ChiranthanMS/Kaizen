from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from services.auth_service import auth_service
from models.user_models import TokenData, UserRole
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Get current authenticated user from JWT token"""
    return auth_service.verify_token(token)

async def get_current_employee(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require employee role"""
    auth_service.require_role(current_user, [UserRole.EMPLOYEE.value])
    return current_user

async def get_current_manager(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require manager role"""
    auth_service.require_role(current_user, [UserRole.MANAGER.value])
    return current_user

async def get_current_employee_or_manager(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Allow both employee and manager roles"""
    auth_service.require_role(current_user, [UserRole.EMPLOYEE.value, UserRole.MANAGER.value])
    return current_user

def require_roles(allowed_roles: List[str]):
    """Decorator factory for role-based access control"""
    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        auth_service.require_role(current_user, allowed_roles)
        return current_user
    return role_checker