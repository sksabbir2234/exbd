"""
Users Router - Exam Prep BD
Admin user management, student approval workflow
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from database.connection import get_db
from database.dependencies import get_current_user, get_admin_user, get_teacher_or_admin
from models import User, UserRole
from schemas import (
    UserResponse, UserUpdate, UserAdminUpdate,
    PaginationParams, PaginationResponse
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=dict)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role: str = None,
    search: str = None,
    is_active: bool = None,
    current_user: User = Depends(get_teacher_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """List users with pagination and filters (teacher/admin)"""
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        query = query.where(
            User.full_name.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%") |
            User.phone.ilike(f"%{search}%")
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Fetch page
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "pagination": PaginationResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        ),
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_teacher_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (teacher/admin)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    update_data: UserAdminUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user role/status (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if update_data.role is not None:
        user.role = UserRole(update_data.role.value)
    if update_data.subscription_tier is not None:
        from models import SubscriptionTier
        user.subscription_tier = SubscriptionTier(update_data.subscription_tier.value)
    if update_data.is_active is not None:
        user.is_active = update_data.is_active
    if update_data.subscription_expires_at is not None:
        user.subscription_expires_at = update_data.subscription_expires_at
    
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a user (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    await db.commit()
    return {"message": "User deactivated"}


@router.get("/students/pending", response_model=List[UserResponse])
async def get_pending_students(
    current_user: User = Depends(get_teacher_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get students pending approval"""
    result = await db.execute(
        select(User)
        .where(User.role == UserRole.STUDENT)
        .where(User.is_verified == False)
        .where(User.is_active == True)
        .order_by(User.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{user_id}/approve", response_model=UserResponse)
async def approve_student(
    user_id: int,
    current_user: User = Depends(get_teacher_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve a student account"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="User is not a student")
    
    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return user
