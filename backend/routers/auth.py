"""
Auth Router - Exam Prep BD
Handles user registration, login, token refresh, password reset
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from database.connection import get_db
from database.dependencies import get_current_user
from models import User, RefreshToken, OTPCode, UserRole, SubscriptionTier
from schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    UserUpdate, PasswordResetRequest, PasswordResetConfirm,
    OTPVerifyRequest, RefreshTokenRequest
)
from utils import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_otp
)
from config.settings import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone already exists (if provided)
    if user_data.phone:
        result = await db.execute(select(User).where(User.phone == user_data.phone))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Create user
    user = User(
        email=user_data.email,
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.STUDENT,
        subscription_tier=SubscriptionTier.FREE,
        is_verified=False,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db), request: Request = None):
    """Login and get access/refresh tokens"""
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store refresh token
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    stored_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("User-Agent") if request else None,
    )
    db.add(stored_token)
    
    # Revoke old tokens (keep last 5)
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .order_by(RefreshToken.created_at.desc())
        .offset(5)
    )
    old_tokens = result.scalars().all()
    for old_token in old_tokens:
        old_token.is_revoked = True
    
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token"""
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token_data.refresh_token)
    )
    refresh_token_obj = result.scalar_one_or_none()
    
    if not refresh_token_obj or refresh_token_obj.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if refresh_token_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode to get user ID
    payload = decode_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    
    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Revoke old refresh token and store new one
    refresh_token_obj.is_revoked = True
    
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_token_obj = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=expires_at,
    )
    db.add(new_token_obj)
    
    await db.commit()
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    
    if update_data.phone is not None:
        # Check if phone is taken by another user
        result = await db.execute(
            select(User).where(User.phone == update_data.phone, User.id != current_user.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already in use"
            )
        current_user.phone = update_data.phone
    
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/logout")
async def logout(
    token_data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout by revoking refresh token"""
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token_data.refresh_token)
    )
    refresh_token_obj = result.scalar_one_or_none()
    
    if refresh_token_obj and refresh_token_obj.user_id == current_user.id:
        refresh_token_obj.is_revoked = True
        await db.commit()
    
    return {"message": "Successfully logged out"}


@router.post("/request-password-reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset OTP"""
    result = await db.execute(select(User).where(User.email == reset_data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, an OTP has been sent"}
    
    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    otp = OTPCode(
        email=user.email,
        code=otp_code,
        purpose="reset_password",
        expires_at=expires_at,
    )
    db.add(otp)
    await db.commit()
    
    # TODO: Send email with OTP
    # For now, just return success message
    return {"message": "If the email exists, an OTP has been sent"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with OTP"""
    # Find valid OTP
    result = await db.execute(
        select(OTPCode)
        .where(OTPCode.code == reset_data.token)
        .where(OTPCode.purpose == "reset_password")
        .where(OTPCode.is_used == False)
        .where(OTPCode.expires_at > datetime.utcnow())
        .order_by(OTPCode.created_at.desc())
    )
    otp = result.scalar_one_or_none()
    
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Find user
    result = await db.execute(select(User).where(User.email == otp.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = hash_password(reset_data.new_password)
    otp.is_used = True
    
    await db.commit()
    
    return {"message": "Password reset successfully"}


@router.post("/send-otp")
async def send_otp(
    otp_request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send OTP for verification"""
    email = otp_request.email
    phone = otp_request.phone
    
    if not email and not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone must be provided"
        )
    
    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    otp = OTPCode(
        email=email,
        phone=phone,
        code=otp_code,
        purpose=otp_request.purpose,
        expires_at=expires_at,
    )
    db.add(otp)
    await db.commit()
    
    # TODO: Send OTP via email/SMS
    return {"message": "OTP sent successfully"}


@router.post("/verify-otp")
async def verify_otp(
    otp_request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify OTP"""
    # Find valid OTP
    query = (
        select(OTPCode)
        .where(OTPCode.code == otp_request.code)
        .where(OTPCode.purpose == otp_request.purpose)
        .where(OTPCode.is_used == False)
        .where(OTPCode.expires_at > datetime.utcnow())
    )
    
    if otp_request.email:
        query = query.where(OTPCode.email == otp_request.email)
    if otp_request.phone:
        query = query.where(OTPCode.phone == otp_request.phone)
    
    result = await db.execute(query.order_by(OTPCode.created_at.desc()))
    otp = result.scalar_one_or_none()
    
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Mark as used
    otp.is_used = True
    await db.commit()
    
    return {"message": "OTP verified successfully"}
