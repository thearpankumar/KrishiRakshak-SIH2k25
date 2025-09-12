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

from ..core.database import get_session
from ..core.dependencies import get_current_active_user
from ..core.config import settings
from ..models.database import User, ImageAnalysis
from ..models.schemas import (
    ImageAnalysis as ImageAnalysisSchema,
    ImageAnalysisCreate,
)
from ..services.ai_service import ai_service
from ..services.image_service import image_service

router = APIRouter()

@router.post("/upload-image", response_model=ImageAnalysisSchema)
async def upload_and_analyze_image(
    analysis_type: str = Form(...),  # 'crop', 'pest', 'disease', 'soil'
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Upload and analyze an image for crop, pest, disease, or soil analysis."""
    
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
        
        # Reset file pointer and reopen for processing
        image = Image.open(io.BytesIO(contents))
        
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
        # Process image with AI service
        analysis_result = await image_service.analyze_image(
            image_path=file_path,
            analysis_type=analysis_type,
            user=current_user
        )
        
        # Save analysis to database
        db_analysis = ImageAnalysis(
            user_id=current_user.id,
            image_path=file_path,
            analysis_type=analysis_type,
            results=analysis_result["results"],
            confidence_score=analysis_result["confidence_score"],
            recommendations=analysis_result["recommendations"]
        )
        
        session.add(db_analysis)
        await session.commit()
        await session.refresh(db_analysis)
        
        return db_analysis
        
    except Exception as e:
        # Clean up uploaded file if processing fails
        try:
            os.remove(file_path)
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image analysis failed: {str(e)}"
        )

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
    """Upload and analyze multiple images at once."""
    
    if len(files) > 10:  # Limit batch size
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 images allowed per batch"
        )
    
    results = []
    
    for file in files:
        try:
            # Process each file similar to single upload
            # This is a simplified version - you might want to optimize for batch processing
            
            if not file.content_type or not file.content_type.startswith('image/'):
                results.append({"filename": file.filename, "error": "Invalid file type"})
                continue
            
            contents = await file.read()
            if len(contents) > settings.max_file_size:
                results.append({"filename": file.filename, "error": "File too large"})
                continue
            
            # Generate unique filename and save
            file_extension = os.path.splitext(file.filename)[1].lower() or '.jpg'
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.upload_dir, unique_filename)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(contents)
            
            # Analyze image
            analysis_result = await image_service.analyze_image(
                image_path=file_path,
                analysis_type=analysis_type,
                user=current_user
            )
            
            # Save to database
            db_analysis = ImageAnalysis(
                user_id=current_user.id,
                image_path=file_path,
                analysis_type=analysis_type,
                results=analysis_result["results"],
                confidence_score=analysis_result["confidence_score"],
                recommendations=analysis_result["recommendations"]
            )
            
            session.add(db_analysis)
            
            results.append({
                "filename": file.filename,
                "analysis_id": str(db_analysis.id),
                "confidence": analysis_result["confidence_score"],
                "success": True
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e),
                "success": False
            })
    
    await session.commit()
    
    return {"results": results}

@router.get("/stats/summary")
async def get_analysis_stats(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get analysis statistics for the current user."""
    
    # Get total analyses by type
    result = await session.execute(
        select(ImageAnalysis.analysis_type, ImageAnalysis.id)
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
        "recent_analyses": len([a for a in analyses if (datetime.utcnow() - a.created_at).days <= 7]) if analyses else 0
    }
    
    for analysis in analyses:
        if analysis.analysis_type in stats["by_type"]:
            stats["by_type"][analysis.analysis_type] += 1
    
    return stats