from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
import httpx
import uuid
from datetime import datetime
from ..core.database import get_session
from ..core.dependencies import get_current_active_user
from ..models.database import User, UserProfile, ChatMessage
from ..models.schemas import ChatMessage as ChatMessageSchema

router = APIRouter()

@router.post("/")
async def send_chat_message(
    message_data: dict,  # Using dict for flexibility with N8N integration
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Send a chat message and get enhanced AI response via N8N."""

    message = message_data.get("message")
    message_type = message_data.get("message_type", "text")

    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content is required"
        )

    # Get user profile for context
    profile_result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    user_profile = profile_result.scalar_one_or_none()

    try:
        # Trigger N8N enhanced chat workflow
        from .triggers import call_n8n_webhook

        enhanced_data = {
            "user_id": str(current_user.id),
            "message": message,
            "message_type": message_type,
            "context": message_data.get("context", {}),
            "user_profile": {
                "crop_types": user_profile.crops_grown if user_profile else [],
                "farm_size": user_profile.farm_size if user_profile else None,
                "farming_experience": user_profile.farming_experience if user_profile else None,
                "preferred_language": user_profile.preferred_language if user_profile else "english"
            } if user_profile else {},
            "user_location": current_user.location,
            "chat_id": f"chat_{uuid.uuid4()}",
            "timestamp": datetime.utcnow().isoformat()
        }

        trigger_result = await call_n8n_webhook("enhanced-chat", enhanced_data, timeout=45.0)

        return {
            "status": "enhanced_response",
            "message": "Enhanced AI processing completed",
            "response": trigger_result.get("ai_response", "Processing..."),
            "trust_score": trigger_result.get("trust_score", 0.8),
            "enhanced_processing": True,
            "context_aware": True,
            "trigger_result": trigger_result
        }

    except Exception as e:
        # Fallback to basic response if N8N is unavailable
        return await _basic_chat_fallback(message, message_type, current_user, user_profile, session)


async def _basic_chat_fallback(
    message: str,
    message_type: str,
    current_user: User,
    user_profile: UserProfile,
    session: AsyncSession
):
    """Fallback to basic chat response when N8N is unavailable."""

    # Basic response logic - you can keep some simple responses here
    basic_response = {
        "response": "I've received your message. Our enhanced AI system will process this shortly.",
        "trust_score": 0.6
    }

    # Save basic chat message to database
    db_message = ChatMessage(
        user_id=current_user.id,
        message=message,
        message_type=message_type,
        response=basic_response["response"],
        trust_score=basic_response["trust_score"]
    )

    session.add(db_message)
    await session.commit()
    await session.refresh(db_message)

    return {
        "id": str(db_message.id),
        "message": message,
        "response": basic_response["response"],
        "trust_score": basic_response["trust_score"],
        "enhanced_processing": False,
        "fallback_mode": True
    }

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