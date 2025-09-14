from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
import httpx
import uuid

from ..core.database import get_session
from ..core.dependencies import get_current_active_user
from ..models.database import User, GroupChat, GroupMessage
from ..models.schemas import (
    GroupChat as GroupChatSchema,
    GroupChatCreate,
    GroupMessage as GroupMessageSchema
)

router = APIRouter()

# Group Chat Management
@router.post("/groups", response_model=GroupChatSchema)
async def create_group_chat(
    group_data: GroupChatCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new group chat."""
    
    # Create group chat
    db_group = GroupChat(
        name=group_data.name,
        description=group_data.description,
        crop_type=group_data.crop_type,
        location=group_data.location
    )
    
    session.add(db_group)
    await session.commit()
    await session.refresh(db_group)
    
    return db_group

@router.get("/groups", response_model=List[GroupChatSchema])
async def get_group_chats(
    crop_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Get list of group chats with optional filtering."""
    
    query = select(GroupChat).where(GroupChat.is_active == is_active)
    
    # Apply filters
    if crop_type:
        query = query.where(GroupChat.crop_type == crop_type)
    if location:
        query = query.where(func.lower(GroupChat.location).contains(location.lower()))
    
    # Order by creation date (newest first)
    query = query.order_by(desc(GroupChat.created_at)).offset(skip).limit(limit)
    
    result = await session.execute(query)
    groups = result.scalars().all()
    
    return groups

@router.get("/groups/{group_id}", response_model=GroupChatSchema)
async def get_group_chat(
    group_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific group chat by ID."""
    
    result = await session.execute(
        select(GroupChat).where(GroupChat.id == group_id)
    )
    
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group chat not found"
        )
    
    return group

@router.put("/groups/{group_id}", response_model=GroupChatSchema)
async def update_group_chat(
    group_id: str,
    group_update: GroupChatCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Update a group chat (admin functionality)."""
    
    result = await session.execute(
        select(GroupChat).where(GroupChat.id == group_id)
    )
    
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group chat not found"
        )
    
    # Update fields
    group.name = group_update.name
    group.description = group_update.description
    group.crop_type = group_update.crop_type
    group.location = group_update.location
    
    await session.commit()
    await session.refresh(group)
    
    return group

@router.delete("/groups/{group_id}")
async def delete_group_chat(
    group_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a group chat (admin functionality)."""
    
    result = await session.execute(
        select(GroupChat).where(GroupChat.id == group_id)
    )
    
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group chat not found"
        )
    
    # Mark as inactive instead of deleting
    group.is_active = False
    await session.commit()
    
    return {"message": "Group chat deactivated successfully"}

# Group Messages
@router.post("/groups/{group_id}/messages")
async def send_group_message(
    group_id: str,
    message_data: dict,  # Using dict for flexibility
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Send a message to a group chat with AI content moderation."""

    message_content = message_data.get("message")
    message_type = message_data.get("message_type", "text")

    if not message_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content is required"
        )

    # Verify group exists and is active
    group_result = await session.execute(
        select(GroupChat).where(
            GroupChat.id == group_id,
            GroupChat.is_active == True
        )
    )

    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group chat not found or inactive"
        )

    # Trigger content moderation via N8N
    try:
        from .triggers import call_n8n_webhook

        enhanced_data = {
            "user_id": str(current_user.id),
            "content": message_content,
            "content_type": "group_message",
            "group_id": group_id,
            "user_reputation": getattr(current_user, 'reputation_score', 0.5),
            "moderation_id": f"mod_{uuid.uuid4()}",
            "timestamp": datetime.utcnow().isoformat()
        }

        moderation_result = await call_n8n_webhook("moderate-content", enhanced_data)

        action = moderation_result.get("action", "approve")

        # Check moderation result
        if action == "reject":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message violates community guidelines and cannot be posted"
            )
        elif action == "review":
            # Queue for human review - don't post immediately
            return {
                "status": "pending_review",
                "message": "Message is being reviewed and will be posted after approval",
                "review_id": moderation_result.get("moderation_id"),
                "estimated_review_time": "5-15 minutes"
            }

    except Exception as e:
        # If moderation fails, allow the message but log the failure
        print(f"Content moderation failed for user {current_user.id} - allowing message: {str(e)}")

    # Create and save the message (if approved or moderation failed)
    db_message = GroupMessage(
        group_id=group_id,
        user_id=current_user.id,
        message=message_content,
        message_type=message_type
    )

    session.add(db_message)
    await session.commit()

    # Reload with user relationship
    await session.refresh(db_message)
    result = await session.execute(
        select(GroupMessage)
        .options(selectinload(GroupMessage.user))
        .where(GroupMessage.id == db_message.id)
    )
    message_with_user = result.scalar_one()

    return {
        "id": str(message_with_user.id),
        "group_id": group_id,
        "user_id": str(message_with_user.user_id),
        "message": message_with_user.message,
        "message_type": message_with_user.message_type,
        "created_at": message_with_user.created_at,
        "user": {
            "id": str(message_with_user.user.id),
            "full_name": message_with_user.user.full_name
        } if message_with_user.user else None,
        "moderated": True,
        "status": "approved"
    }

@router.get("/groups/{group_id}/messages", response_model=List[GroupMessageSchema])
async def get_group_messages(
    group_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get messages from a group chat."""
    
    # Verify group exists
    group_result = await session.execute(
        select(GroupChat).where(GroupChat.id == group_id)
    )
    
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group chat not found"
        )
    
    # Get messages with user information
    result = await session.execute(
        select(GroupMessage)
        .options(selectinload(GroupMessage.user))
        .where(GroupMessage.group_id == group_id)
        .order_by(desc(GroupMessage.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    messages = result.scalars().all()
    return messages

@router.get("/groups/{group_id}/messages/{message_id}", response_model=GroupMessageSchema)
async def get_group_message(
    group_id: str,
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific group message."""
    
    result = await session.execute(
        select(GroupMessage)
        .options(selectinload(GroupMessage.user))
        .where(
            GroupMessage.id == message_id,
            GroupMessage.group_id == group_id
        )
    )
    
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return message

@router.delete("/groups/{group_id}/messages/{message_id}")
async def delete_group_message(
    group_id: str,
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a group message (only by message author)."""
    
    result = await session.execute(
        select(GroupMessage).where(
            GroupMessage.id == message_id,
            GroupMessage.group_id == group_id
        )
    )
    
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if current user is the author of the message
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages"
        )
    
    await session.delete(message)
    await session.commit()
    
    return {"message": "Group message deleted successfully"}

# Group Statistics and Discovery
@router.get("/groups/{group_id}/stats")
async def get_group_stats(
    group_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get statistics for a group chat."""
    
    # Verify group exists
    group_result = await session.execute(
        select(GroupChat).where(GroupChat.id == group_id)
    )
    
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group chat not found"
        )
    
    # Get message count
    message_count_result = await session.execute(
        select(func.count(GroupMessage.id)).where(GroupMessage.group_id == group_id)
    )
    message_count = message_count_result.scalar()
    
    # Get active users count (users who sent messages in last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    active_users_result = await session.execute(
        select(func.count(func.distinct(GroupMessage.user_id)))
        .where(
            GroupMessage.group_id == group_id,
            GroupMessage.created_at >= week_ago
        )
    )
    active_users = active_users_result.scalar()
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        "total_messages": message_count,
        "active_users_this_week": active_users,
        "created_at": group.created_at
    }

@router.get("/discover")
async def discover_groups(
    user_crop_types: Optional[List[str]] = Query(None),
    user_location: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Discover relevant groups based on user interests."""
    
    query = select(GroupChat).where(GroupChat.is_active == True)
    
    # Priority scoring based on user profile
    conditions = []
    
    # Prefer groups with matching crop types
    if user_crop_types:
        crop_conditions = [
            GroupChat.crop_type == crop for crop in user_crop_types
        ]
        if crop_conditions:
            conditions.extend(crop_conditions)
    
    # Prefer groups with matching or nearby location
    if user_location:
        location_condition = func.lower(GroupChat.location).contains(user_location.lower())
        conditions.append(location_condition)
    
    if conditions:
        # Use OR to match any of the conditions
        query = query.where(or_(*conditions))
    
    # Order by creation date for now (could be enhanced with activity metrics)
    query = query.order_by(desc(GroupChat.created_at)).limit(limit)
    
    result = await session.execute(query)
    recommended_groups = result.scalars().all()
    
    return {
        "recommended_groups": recommended_groups,
        "recommendation_basis": {
            "crop_types": user_crop_types,
            "location": user_location
        }
    }

@router.get("/my-groups", response_model=List[GroupChatSchema])
async def get_my_groups(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get groups where the current user has participated."""
    
    # Find groups where user has sent messages
    result = await session.execute(
        select(GroupChat)
        .join(GroupMessage, GroupChat.id == GroupMessage.group_id)
        .where(
            GroupMessage.user_id == current_user.id,
            GroupChat.is_active == True
        )
        .distinct()
        .order_by(desc(GroupChat.created_at))
    )
    
    groups = result.scalars().all()
    return groups

@router.get("/activity-feed")
async def get_activity_feed(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get recent activity from all groups."""
    
    # Get recent messages from all active groups
    result = await session.execute(
        select(GroupMessage)
        .options(
            selectinload(GroupMessage.user),
            selectinload(GroupMessage.group)
        )
        .join(GroupChat, GroupMessage.group_id == GroupChat.id)
        .where(GroupChat.is_active == True)
        .order_by(desc(GroupMessage.created_at))
        .limit(limit)
    )
    
    messages = result.scalars().all()
    
    # Format activity feed
    activity_feed = []
    for message in messages:
        activity_feed.append({
            "id": message.id,
            "type": "group_message",
            "message": message.message[:100] + "..." if len(message.message) > 100 else message.message,
            "user_name": message.user.full_name,
            "group_name": message.group.name,
            "group_id": message.group_id,
            "created_at": message.created_at
        })
    
    return {"activity_feed": activity_feed}

@router.get("/popular-topics")
async def get_popular_topics(
    days: int = Query(7, ge=1, le=30),
    session: AsyncSession = Depends(get_session)
):
    """Get popular discussion topics based on group activity."""
    
    from datetime import datetime, timedelta
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get crop types from active groups
    crop_result = await session.execute(
        select(GroupChat.crop_type, func.count(GroupMessage.id).label('message_count'))
        .join(GroupMessage, GroupChat.id == GroupMessage.group_id)
        .where(
            GroupChat.is_active == True,
            GroupChat.crop_type.is_not(None),
            GroupMessage.created_at >= since_date
        )
        .group_by(GroupChat.crop_type)
        .order_by(desc('message_count'))
        .limit(10)
    )
    
    popular_crops = crop_result.all()
    
    # Get locations from active groups  
    location_result = await session.execute(
        select(GroupChat.location, func.count(GroupMessage.id).label('message_count'))
        .join(GroupMessage, GroupChat.id == GroupMessage.group_id)
        .where(
            GroupChat.is_active == True,
            GroupChat.location.is_not(None),
            GroupMessage.created_at >= since_date
        )
        .group_by(GroupChat.location)
        .order_by(desc('message_count'))
        .limit(10)
    )
    
    popular_locations = location_result.all()
    
    return {
        "popular_crops": [{"name": crop.crop_type, "activity": crop.message_count} for crop in popular_crops],
        "popular_locations": [{"name": loc.location, "activity": loc.message_count} for loc in popular_locations],
        "period_days": days
    }