from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_session
from ..core.security import verify_password, get_password_hash, create_access_token
from ..core.config import settings
from ..core.dependencies import get_current_active_user
from ..models.database import User, UserProfile, ChatMessage
from ..models.schemas import (
    User as UserSchema, 
    UserCreate, 
    UserUpdate,
    UserProfile as UserProfileSchema,
    UserProfileCreate,
    UserProfileUpdate,
    Token
)

router = APIRouter()

@router.post("/register", response_model=UserSchema)
async def register_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """Register a new user."""
    # Check if user already exists
    result = await session.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone number already exists (if provided)
    if user_data.phone_number:
        result = await session.execute(select(User).where(User.phone_number == user_data.phone_number))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        location=user_data.location,
        latitude=user_data.latitude,
        longitude=user_data.longitude,
    )
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    """Login user and return access token."""
    # Get user by email
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile."""
    return current_user

@router.put("/me", response_model=UserSchema)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Update current user profile."""
    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await session.commit()
    await session.refresh(current_user)
    
    return current_user

@router.post("/profile", response_model=UserProfileSchema)
async def create_user_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Create user farming profile."""
    # Check if profile already exists
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile already exists"
        )
    
    # Create new profile
    db_profile = UserProfile(
        user_id=current_user.id,
        **profile_data.model_dump()
    )
    
    session.add(db_profile)
    await session.commit()
    await session.refresh(db_profile)
    
    return db_profile

@router.get("/profile", response_model=UserProfileSchema)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get user farming profile."""
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return profile

@router.put("/profile", response_model=UserProfileSchema)
async def update_user_profile_farming(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Update user farming profile."""
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Update profile fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    await session.commit()
    await session.refresh(profile)
    
    return profile

@router.delete("/me")
async def delete_user_account(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete current user account and all associated data."""
    
    # Delete chat messages first
    chat_result = await session.execute(
        select(ChatMessage).where(ChatMessage.user_id == current_user.id)
    )
    chat_messages = chat_result.scalars().all()
    for message in chat_messages:
        await session.delete(message)
    
    # Delete user profile (if exists)
    profile_result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        await session.delete(profile)
    
    # Delete user account
    await session.delete(current_user)
    await session.commit()
    
    return {"message": "User account deleted successfully"}

@router.delete("/profile")
async def delete_user_profile_farming(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete user farming profile."""
    
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    await session.delete(profile)
    await session.commit()
    
    return {"message": "User profile deleted successfully"}