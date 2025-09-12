from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from ..core.database import get_session
from ..core.dependencies import get_current_active_user
from ..models.database import User, UserProfile, ChatMessage
from ..models.schemas import (
    ChatMessage as ChatMessageSchema,
    ChatMessageCreate,
)
from ..services.ai_service import ai_service

router = APIRouter()

@router.post("/", response_model=ChatMessageSchema)
async def send_chat_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Send a chat message and get AI response."""
    
    # Get user profile for context
    profile_result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    user_profile = profile_result.scalar_one_or_none()
    
    # Process message with AI service
    ai_response = await ai_service.process_chat_message(
        message=message_data.message,
        message_type=message_data.message_type,
        user=current_user,
        user_profile=user_profile
    )
    
    # Save chat message to database
    db_message = ChatMessage(
        user_id=current_user.id,
        message=message_data.message,
        message_type=message_data.message_type,
        response=ai_response["response"],
        trust_score=ai_response["trust_score"]
    )
    
    session.add(db_message)
    await session.commit()
    await session.refresh(db_message)
    
    return db_message

@router.get("/history", response_model=List[ChatMessageSchema])
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get user's chat history."""
    
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(desc(ChatMessage.created_at))
        .limit(limit)
        .offset(offset)
    )
    
    messages = result.scalars().all()
    return messages

@router.get("/{message_id}", response_model=ChatMessageSchema)
async def get_chat_message(
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific chat message."""
    
    result = await session.execute(
        select(ChatMessage)
        .where(
            ChatMessage.id == message_id,
            ChatMessage.user_id == current_user.id
        )
    )
    
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return message

@router.delete("/{message_id}")
async def delete_chat_message(
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a chat message."""
    
    result = await session.execute(
        select(ChatMessage)
        .where(
            ChatMessage.id == message_id,
            ChatMessage.user_id == current_user.id
        )
    )
    
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    await session.delete(message)
    await session.commit()
    
    return {"message": "Chat message deleted successfully"}

@router.delete("/history/clear")
async def clear_chat_history(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Clear all chat history for the current user."""
    
    result = await session.execute(
        select(ChatMessage).where(ChatMessage.user_id == current_user.id)
    )
    
    messages = result.scalars().all()
    for message in messages:
        await session.delete(message)
    
    await session.commit()
    
    return {"message": f"Cleared {len(messages)} messages from chat history"}