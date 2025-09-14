from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from ..core.database import get_session
from ..models.database import ImageAnalysis, User, GroupMessage, ChatMessage

router = APIRouter()

# Webhook receivers for N8N callbacks

@router.post("/image-analysis")
async def receive_image_analysis_result(
    data: Dict[Any, Any],
    x_workflow_source: Optional[str] = Header(None, alias="X-Workflow-Source"),
    session: AsyncSession = Depends(get_session)
):
    """Receive enhanced image analysis results from N8N"""

    print(f"📥 Received webhook data: {data}")
    print(f"📥 Workflow source header: {x_workflow_source}")

    if x_workflow_source != "n8n-image-analysis":
        print(f"⚠️ Invalid workflow source: {x_workflow_source}")
        raise HTTPException(status_code=401, detail="Invalid workflow source")

    try:
        # Validate required fields
        required_fields = ["user_id", "image_path", "analysis_type", "results", "confidence_score"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Save enhanced analysis result to database
        analysis = ImageAnalysis(
            id=str(uuid.uuid4()),
            user_id=data["user_id"],
            image_path=data["image_path"],
            analysis_type=data["analysis_type"],
            results=data["results"],
            confidence_score=float(data["confidence_score"]),
            recommendations=data.get("recommendations", []),
        )

        # Add enhanced metadata from N8N processing
        if "metadata" in data:
            # Store additional metadata in the results field
            analysis.results.update({
                "enhanced_analysis": True,
                "model_used": data["metadata"].get("model_used", "gpt-4o-mini"),
                "processing_time": data["metadata"].get("processing_time"),
                "local_context": data["metadata"].get("local_context"),
                "seasonal_factors": data["metadata"].get("seasonal_factors"),
                "treatment_plan": data.get("treatment_plan"),
                "prevention_measures": data.get("prevention_measures")
            })

        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        # TODO: Trigger notification to user about completed analysis
        # This could trigger another N8N workflow for notifications

        return {"status": "success", "analysis_id": str(analysis.id)}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save analysis: {str(e)}")

@router.post("/batch-complete")
async def receive_batch_analysis_complete(
    data: Dict[Any, Any],
    x_workflow_source: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session)
):
    """Receive batch analysis completion from N8N"""

    if x_workflow_source != "n8n-batch-analysis":
        raise HTTPException(status_code=401, detail="Invalid workflow source")

    try:
        # Validate batch data
        if "individual_results" not in data or not isinstance(data["individual_results"], list):
            raise HTTPException(status_code=400, detail="Missing or invalid individual_results")

        saved_analyses = []

        # Save individual analysis results
        for result in data["individual_results"]:
            analysis = ImageAnalysis(
                id=str(uuid.uuid4()),
                user_id=result["user_id"],
                image_path=result["image_path"],
                analysis_type=result["analysis_type"],
                results=result["results"],
                confidence_score=float(result["confidence_score"]),
                recommendations=result.get("recommendations", [])
            )

            # Mark as part of batch
            analysis.results.update({
                "batch_id": data.get("batch_id"),
                "batch_processing": True,
                "image_index": result.get("image_index")
            })

            session.add(analysis)
            saved_analyses.append(str(analysis.id))

        # TODO: Create batch summary record
        # TODO: Send notification about batch completion

        await session.commit()

        return {
            "status": "success",
            "batch_id": data.get("batch_id"),
            "processed_count": len(saved_analyses),
            "analysis_ids": saved_analyses
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save batch results: {str(e)}")

@router.post("/community-moderation")
async def receive_moderation_result(
    data: Dict[Any, Any],
    x_workflow_source: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session)
):
    """Receive content moderation results from N8N"""

    if x_workflow_source != "n8n-content-moderation":
        raise HTTPException(status_code=401, detail="Invalid workflow source")

    try:
        moderation_result = data.get("moderation_result", {})
        action = moderation_result.get("action", "approve")
        content_type = data.get("content_type")
        content_id = data.get("content_id")

        if action == "approve":
            # Message is approved - no action needed
            pass
        elif action == "reject":
            # Mark message as rejected/hidden
            if content_type == "group_message" and content_id:
                result = await session.execute(
                    select(GroupMessage).where(GroupMessage.id == content_id)
                )
                message = result.scalar_one_or_none()
                if message:
                    # Add moderation flag to message - you may want to add a status field to your model
                    pass
            elif content_type == "chat_message" and content_id:
                result = await session.execute(
                    select(ChatMessage).where(ChatMessage.id == content_id)
                )
                message = result.scalar_one_or_none()
                if message:
                    # Add moderation flag to message
                    pass
        elif action == "review":
            # Queue for human review
            # TODO: Add to review queue system
            pass

        await session.commit()

        return {
            "status": "success",
            "moderation_id": data.get("moderation_id"),
            "action_taken": action
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process moderation: {str(e)}")

@router.post("/weather-market-update")
async def receive_weather_market_data(
    data: Dict[Any, Any],
    x_workflow_source: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session)
):
    """Receive weather and market data updates from N8N"""

    if x_workflow_source != "n8n-weather-market":
        raise HTTPException(status_code=401, detail="Invalid workflow source")

    try:
        # TODO: Create WeatherData and MarketData models and save
        # For now, we'll just acknowledge the data

        weather_data = data.get("weather_data", {})
        market_data = data.get("market_data", {})
        alerts = data.get("alerts", [])

        # TODO: Save weather data to database
        # weather_record = WeatherData(
        #     location_name=weather_data.get("location"),
        #     temperature=weather_data.get("temperature"),
        #     humidity=weather_data.get("humidity"),
        #     # ... other fields
        # )

        # TODO: Save market data to database
        # if market_data:
        #     for market_item in market_data:
        #         market_record = MarketData(...)

        # TODO: Trigger relevant notifications based on alerts
        # if alerts:
        #     for alert in alerts:
        #         # Trigger notification workflow

        return {
            "status": "success",
            "sync_id": data.get("sync_id"),
            "weather_updated": bool(weather_data),
            "market_updated": bool(market_data),
            "alerts_processed": len(alerts)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save weather/market data: {str(e)}")

@router.post("/notification-delivered")
async def log_notification_delivery(
    data: Dict[Any, Any],
    x_log_type: Optional[str] = Header(None)
):
    """Log notification delivery status"""

    try:
        # TODO: Save notification delivery log
        # This helps track notification performance and user engagement

        notification_id = data.get("notification_id")
        delivery_status = data.get("delivery_status", "delivered")
        delivery_channels = data.get("delivery_channels", [])
        user_id = data.get("user_id")

        # For now, just log the delivery
        # TODO: Create NotificationLog model and save to database

        return {
            "status": "success",
            "logged": True,
            "notification_id": notification_id,
            "delivery_status": delivery_status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log notification: {str(e)}")

@router.post("/enhanced-chat")
async def receive_enhanced_chat_response(
    data: Dict[Any, Any],
    x_workflow_source: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session)
):
    """Receive enhanced chat response from N8N"""

    if x_workflow_source != "n8n-enhanced-chat":
        raise HTTPException(status_code=401, detail="Invalid workflow source")

    try:
        # Save enhanced chat message with AI response
        chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=data["user_id"],
            message=data["original_message"],
            message_type=data.get("message_type", "text"),
            response=data["ai_response"],
            trust_score=float(data.get("trust_score", 0.8))
        )

        # Add enhanced metadata
        if "metadata" in data:
            # You might want to add a metadata field to ChatMessage model
            pass

        session.add(chat_message)
        await session.commit()
        await session.refresh(chat_message)

        return {
            "status": "success",
            "chat_id": data.get("chat_id"),
            "message_id": str(chat_message.id),
            "response": data["ai_response"],
            "trust_score": data.get("trust_score", 0.8)
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save chat response: {str(e)}")

@router.post("/knowledge-query")
async def receive_knowledge_query_response(
    data: Dict[Any, Any],
    x_workflow_source: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session)
):
    """Receive enhanced knowledge query response from N8N"""

    if x_workflow_source != "n8n-knowledge-query":
        raise HTTPException(status_code=401, detail="Invalid workflow source")

    try:
        # TODO: Save enhanced knowledge response
        # This could be saved to QARepository if it's high quality

        answer = data.get("ai_response")
        trust_score = data.get("trust_score", 0.8)

        # If high quality response, save to knowledge base
        if trust_score > 0.8:
            from ..models.database import QARepository
            qa_entry = QARepository(
                id=str(uuid.uuid4()),
                question=data["original_question"],
                answer=answer,
                crop_type=data.get("crop_type"),
                category="ai_generated",
                language=data.get("language", "english")
            )

            session.add(qa_entry)
            await session.commit()

        return {
            "status": "success",
            "query_id": data.get("query_id"),
            "answer": answer,
            "trust_score": trust_score,
            "saved_to_kb": trust_score > 0.8
        }

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save knowledge response: {str(e)}")

@router.get("/health")
async def webhook_health_check():
    """Health check for webhook endpoints"""
    return {
        "status": "healthy",
        "service": "webhook-receiver",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": [
            "/image-analysis",
            "/batch-complete",
            "/community-moderation",
            "/weather-market-update",
            "/notification-delivered",
            "/enhanced-chat",
            "/knowledge-query"
        ]
    }