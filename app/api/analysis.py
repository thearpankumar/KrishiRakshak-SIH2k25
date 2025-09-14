from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
import os
import uuid
from datetime import datetime
import aiofiles
from PIL import Image
import io
import httpx

from ..core.database import get_session
from ..core.dependencies import get_current_active_user
from ..core.config import settings
from ..models.database import User, ImageAnalysis
from ..models.schemas import ImageAnalysis as ImageAnalysisSchema

router = APIRouter()

@router.post("/analyze")
async def analyze_image(
    analysis_type: str = Form(...),  # 'crop', 'pest', 'disease', 'soil'
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Upload and trigger enhanced image analysis via N8N workflow."""
    return await upload_and_trigger_analysis(analysis_type, file, current_user, session)

async def upload_and_trigger_analysis(
    analysis_type: str,
    file: UploadFile,
    current_user: User,
    session: AsyncSession
):
    """Upload image and trigger N8N analysis workflow."""

    # Validate analysis type
    valid_types = ['crop', 'pest', 'disease', 'soil']
    if analysis_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid analysis type. Must be one of: {', '.join(valid_types)}"
        )

    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    # Check file size
    contents = await file.read()
    if len(contents) > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum of {settings.max_file_size} bytes"
        )

    try:
        # Validate image can be opened
        image = Image.open(io.BytesIO(contents))
        image.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )

    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1].lower()
    if not file_extension:
        file_extension = '.jpg'

    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)

    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(contents)

    try:
        # Use internal trigger service for N8N integration
        from .triggers import call_n8n_webhook

        enhanced_data = {
            "user_id": str(current_user.id),
            "image_path": file_path,
            "analysis_type": analysis_type,
            "filename": file.filename,
            "user_location": current_user.location,
            "user_latitude": current_user.latitude,
            "user_longitude": current_user.longitude,
            "timestamp": datetime.utcnow().isoformat()
        }

        trigger_result = await call_n8n_webhook("image-analysis", enhanced_data, timeout=60.0)

        # Return immediate response - actual results will come via webhook
        return {
            "status": "processing",
            "message": "Enhanced image analysis started - you will receive a notification when complete",
            "estimated_time": "2-5 minutes",
            "analysis_id": "pending",
            "workflow_triggered": True,
            "enhanced_processing": True,
            "trigger_result": trigger_result
        }

    except Exception as e:
        # Clean up uploaded file if processing fails
        try:
            os.remove(file_path)
        except:
            pass

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to start enhanced analysis: {str(e)}"
        )

@router.post("/upload-image")
async def upload_and_analyze_image(
    analysis_type: str = Form(...),  # 'crop', 'pest', 'disease', 'soil'
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Upload and analyze an image for crop, pest, disease, or soil analysis."""
    return await upload_and_trigger_analysis(analysis_type, file, current_user, session)

@router.get("/history", response_model=List[ImageAnalysisSchema])
async def get_analysis_history(
    analysis_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get user's image analysis history."""
    
    query = select(ImageAnalysis).where(ImageAnalysis.user_id == current_user.id)
    
    if analysis_type:
        query = query.where(ImageAnalysis.analysis_type == analysis_type)
    
    query = query.order_by(desc(ImageAnalysis.created_at)).limit(limit).offset(offset)
    
    result = await session.execute(query)
    analyses = result.scalars().all()
    
    return analyses

@router.get("/{analysis_id}", response_model=ImageAnalysisSchema)
async def get_analysis_result(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific analysis result."""
    
    result = await session.execute(
        select(ImageAnalysis).where(
            ImageAnalysis.id == analysis_id,
            ImageAnalysis.user_id == current_user.id
        )
    )
    
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return analysis

@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete an analysis result and associated image."""
    
    result = await session.execute(
        select(ImageAnalysis).where(
            ImageAnalysis.id == analysis_id,
            ImageAnalysis.user_id == current_user.id
        )
    )
    
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # Delete image file
    try:
        if os.path.exists(analysis.image_path):
            os.remove(analysis.image_path)
    except Exception:
        pass  # Continue even if file deletion fails
    
    # Delete database record
    await session.delete(analysis)
    await session.commit()
    
    return {"message": "Analysis deleted successfully"}

@router.post("/batch-analyze")
async def batch_analyze_images(
    analysis_type: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Upload and trigger batch image analysis via N8N workflow."""

    if len(files) > 20:  # Increased limit for N8N batch processing
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 images allowed per batch"
        )

    # Validate analysis type
    valid_types = ['crop', 'pest', 'disease', 'soil']
    if analysis_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid analysis type. Must be one of: {', '.join(valid_types)}"
        )

    uploaded_files = []

    # Upload and validate all files first
    for file in files:
        try:
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type for {file.filename}"
                )

            contents = await file.read()
            if len(contents) > settings.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {file.filename} exceeds size limit"
                )

            # Validate image
            try:
                image = Image.open(io.BytesIO(contents))
                image.verify()
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid image file: {file.filename}"
                )

            # Generate unique filename and save
            file_extension = os.path.splitext(file.filename)[1].lower() or '.jpg'
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.upload_dir, unique_filename)

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(contents)

            uploaded_files.append({
                "image_path": file_path,
                "filename": file.filename
            })

        except HTTPException:
            # Clean up any already uploaded files on error
            for uploaded in uploaded_files:
                try:
                    os.remove(uploaded["image_path"])
                except:
                    pass
            raise
        except Exception as e:
            # Clean up any already uploaded files on error
            for uploaded in uploaded_files:
                try:
                    os.remove(uploaded["image_path"])
                except:
                    pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process {file.filename}: {str(e)}"
            )

    # Trigger N8N batch analysis workflow
    try:
        from .triggers import call_n8n_webhook

        enhanced_data = {
            "user_id": str(current_user.id),
            "analysis_type": analysis_type,
            "images": uploaded_files,
            "batch_id": f"batch_{uuid.uuid4()}",
            "user_location": current_user.location,
            "timestamp": datetime.utcnow().isoformat()
        }

        trigger_result = await call_n8n_webhook("batch-analysis", enhanced_data, timeout=300.0)

        return {
            "status": "processing",
            "message": f"Enhanced batch analysis started for {len(uploaded_files)} images",
            "estimated_time": f"{len(uploaded_files) * 2}-{len(uploaded_files) * 5} minutes",
            "batch_size": len(uploaded_files),
            "workflow_triggered": True,
            "enhanced_processing": True,
            "trigger_result": trigger_result
        }

    except Exception as e:
        # Clean up files if request fails
        for uploaded in uploaded_files:
            try:
                os.remove(uploaded["image_path"])
            except:
                pass

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to start batch analysis: {str(e)}"
        )

@router.get("/stats/summary")
async def get_analysis_stats(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get analysis statistics for the current user."""
    
    # Get total analyses by type
    result = await session.execute(
        select(ImageAnalysis.analysis_type, ImageAnalysis.id, ImageAnalysis.created_at)
        .where(ImageAnalysis.user_id == current_user.id)
    )
    
    analyses = result.all()
    
    stats = {
        "total_analyses": len(analyses),
        "by_type": {
            "crop": 0,
            "pest": 0,
            "disease": 0,
            "soil": 0
        },
        "recent_analyses": len([a for a in analyses if (datetime.now().replace(tzinfo=None) - a.created_at.replace(tzinfo=None)).days <= 7]) if analyses else 0
    }
    
    for analysis in analyses:
        if analysis.analysis_type in stats["by_type"]:
            stats["by_type"][analysis.analysis_type] += 1
    
    return stats