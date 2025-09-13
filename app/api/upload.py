from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
import os
import uuid
import aiofiles
from PIL import Image
import io

from ..core.database import get_session
from ..core.dependencies import get_current_active_user
from ..core.config import settings
from ..models.database import User

router = APIRouter()

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, str]:
    """Upload a file and return the file path."""

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

    try:
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(contents)

        # Return relative path for frontend
        relative_path = f"uploads/{unique_filename}"

        return {"file_path": relative_path}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )