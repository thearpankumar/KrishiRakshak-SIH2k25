from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import asyncio
from typing import Dict, Any, List, Optional
import uuid
import os
from datetime import datetime

from ..core.database import get_session
from ..core.dependencies import get_current_active_user
from ..core.config import settings
from ..models.database import User

router = APIRouter()

async def call_n8n_webhook(webhook_path: str, data: Dict[Any, Any], timeout: float = 30.0):
    """Helper function to call N8N webhooks"""
    webhook_url = f"{settings.n8n_webhook_base_url}/{webhook_path}"

    print(f"🔗 N8N Webhook URL: {webhook_url}")
    print(f"📤 Data being sent to N8N: {data}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(webhook_url, json=data, timeout=timeout)
            print(f"📡 N8N Response Status: {response.status_code}")
            print(f"📡 N8N Response Headers: {response.headers}")

            response_text = response.text
            print(f"📡 N8N Raw Response: {response_text}")

            response.raise_for_status()

            if not response_text.strip():
                print("⚠️ N8N returned empty response")
                return {"status": "success", "message": "N8N webhook called but returned empty response"}

            return response.json()
        except httpx.TimeoutException:
            print("⏰ N8N Webhook timeout")
            raise HTTPException(status_code=408, detail="N8N workflow timeout")
        except httpx.RequestError as e:
            print(f"🚫 N8N Request Error: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Failed to call N8N: {str(e)}")
        except httpx.HTTPStatusError as e:
            print(f"❌ N8N HTTP Status Error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"N8N workflow error: {e.response.text}")
        except ValueError as e:
            print(f"🔍 N8N JSON Parse Error: {str(e)}")
            print(f"🔍 Response was: {response_text}")
            raise HTTPException(status_code=503, detail=f"Failed to parse N8N response: {str(e)}")

@router.post("/analyze-image")
async def trigger_image_analysis(
    image_path: str = Form(...),
    analysis_type: str = Form(...),
    filename: str = Form(...),
    current_user: User = Depends(get_current_active_user)
):
    """Trigger enhanced image analysis workflow"""

    # Validate analysis type
    valid_types = ['crop', 'pest', 'disease', 'soil']
    if analysis_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid analysis type. Must be one of: {', '.join(valid_types)}"
        )

    # Check if file exists
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    enhanced_data = {
        "user_id": str(current_user.id),
        "image_path": image_path,
        "analysis_type": analysis_type,
        "filename": filename,
        "user_location": current_user.location,
        "user_latitude": current_user.latitude,
        "user_longitude": current_user.longitude,
        "timestamp": datetime.utcnow().isoformat()
    }

    return await call_n8n_webhook("image-analysis", enhanced_data, timeout=60.0)

@router.post("/batch-analyze")
async def trigger_batch_analysis(
    analysis_type: str = Form(...),
    image_data: List[Dict[str, str]] = Form(...),  # List of {"image_path": str, "filename": str}
    current_user: User = Depends(get_current_active_user)
):
    """Trigger batch image analysis workflow"""

    # Validate analysis type
    valid_types = ['crop', 'pest', 'disease', 'soil']
    if analysis_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid analysis type. Must be one of: {', '.join(valid_types)}"
        )

    # Validate batch size
    if len(image_data) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 images allowed per batch")

    enhanced_data = {
        "user_id": str(current_user.id),
        "analysis_type": analysis_type,
        "images": image_data,
        "batch_id": f"batch_{uuid.uuid4()}",
        "user_location": current_user.location,
        "timestamp": datetime.utcnow().isoformat()
    }

    return await call_n8n_webhook("batch-analysis", enhanced_data, timeout=300.0)

@router.post("/moderate-content")
async def trigger_content_moderation(
    content: str = Form(...),
    content_type: str = Form(...),  # 'group_message', 'chat_message', 'user_profile'
    group_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """Trigger content moderation workflow"""

    valid_content_types = ['group_message', 'chat_message', 'user_profile']
    if content_type not in valid_content_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Must be one of: {', '.join(valid_content_types)}"
        )

    enhanced_data = {
        "user_id": str(current_user.id),
        "content": content,
        "content_type": content_type,
        "group_id": group_id,
        "user_reputation": getattr(current_user, 'reputation_score', 0.5),
        "moderation_id": f"mod_{uuid.uuid4()}",
        "timestamp": datetime.utcnow().isoformat()
    }

    return await call_n8n_webhook("moderate-content", enhanced_data)

@router.post("/send-notification")
async def trigger_smart_notification(
    notification_type: str = Form(...),
    message: str = Form(...),
    priority: str = Form("medium"),
    target_user_id: Optional[str] = Form(None),
    metadata: Optional[Dict[str, Any]] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """Trigger smart notification workflow"""

    valid_types = [
        'weather_alert', 'market_update', 'crop_analysis_complete',
        'community_message', 'system_alert', 'agricultural_tip',
        'price_alert', 'seasonal_reminder'
    ]

    if notification_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid notification type. Must be one of: {', '.join(valid_types)}"
        )

    valid_priorities = ['low', 'medium', 'high', 'urgent']
    if priority not in valid_priorities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        )

    enhanced_data = {
        "user_id": target_user_id or str(current_user.id),
        "notification_type": notification_type,
        "message": message,
        "priority": priority,
        "metadata": metadata or {},
        "sender_id": str(current_user.id),
        "timestamp": datetime.utcnow().isoformat()
    }

    return await call_n8n_webhook("send-notification", enhanced_data)

@router.post("/update-weather")
async def trigger_weather_update(
    location: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    current_user: User = Depends(get_current_active_user)
):
    """Trigger weather and market data update"""

    # Use user location if not provided
    if not location and not (latitude and longitude):
        location = current_user.location
        latitude = current_user.latitude
        longitude = current_user.longitude

    trigger_data = {
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "requested_by": str(current_user.id),
        "sync_id": f"sync_{uuid.uuid4()}",
        "timestamp": datetime.utcnow().isoformat()
    }

    return await call_n8n_webhook("weather-market-sync", trigger_data)

@router.post("/enhance-chat")
async def trigger_enhanced_chat(
    message: str = Form(...),
    message_type: str = Form("text"),
    context: Optional[Dict[str, Any]] = Form(None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Trigger enhanced chat processing with AI"""

    # Get user profile for context
    from sqlalchemy import select
    from ..models.database import UserProfile

    profile_result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    user_profile = profile_result.scalar_one_or_none()

    enhanced_data = {
        "user_id": str(current_user.id),
        "message": message,
        "message_type": message_type,
        "context": context or {},
        "user_profile": {
            "crop_types": user_profile.crop_types if user_profile else [],
            "farm_size": user_profile.farm_size if user_profile else None,
            "farming_experience": user_profile.farming_experience if user_profile else None,
            "preferred_language": user_profile.preferred_language if user_profile else "english"
        } if user_profile else {},
        "user_location": current_user.location,
        "chat_id": f"chat_{uuid.uuid4()}",
        "timestamp": datetime.utcnow().isoformat()
    }

    return await call_n8n_webhook("enhanced-chat", enhanced_data, timeout=45.0)

@router.post("/process-knowledge-query")
async def trigger_knowledge_processing(
    question: str = Form(...),
    crop_type: Optional[str] = Form(None),
    language: str = Form("english"),
    current_user: User = Depends(get_current_active_user)
):
    """Trigger enhanced knowledge base processing"""

    enhanced_data = {
        "user_id": str(current_user.id),
        "question": question,
        "crop_type": crop_type,
        "language": language,
        "user_location": current_user.location,
        "query_id": f"knowledge_{uuid.uuid4()}",
        "timestamp": datetime.utcnow().isoformat()
    }

    return await call_n8n_webhook("knowledge-query", enhanced_data, timeout=60.0)

@router.get("/health")
async def check_n8n_connectivity():
    """Check N8N connectivity and workflow status"""
    try:
        # Test basic connectivity
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.n8n_webhook_base_url}/health-check", timeout=10.0)
            return {
                "status": "connected",
                "n8n_status": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }