"""
Dependencies - Exam Prep BD
Common dependencies for API endpoints
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from jose import jwt

from database.connection import get_db
from config.settings import get_settings
from models import User, UserRole
from utils import decode_token

settings = get_settings()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get the current user if authenticated, otherwise return None"""
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def require_role(required_role: UserRole):
    """Dependency factory to require a specific user role"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_hierarchy = {
            UserRole.ADMIN: [UserRole.ADMIN],
            UserRole.TEACHER: [UserRole.ADMIN, UserRole.TEACHER],
            UserRole.STUDENT: [UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT],
        }
        
        allowed_roles = role_hierarchy.get(required_role, [required_role])
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role.value}",
            )
        return current_user
    
    return role_checker


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_teacher_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require teacher or admin role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin access required",
        )
    return current_user


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")
