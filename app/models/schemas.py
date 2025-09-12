from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class User(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# User Profile schemas
class UserProfileBase(BaseModel):
    crops_grown: Optional[List[str]] = None
    farm_size: Optional[float] = None
    farming_experience: Optional[int] = None
    preferred_language: Optional[str] = "malayalam"

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# Chat schemas
class ChatMessageBase(BaseModel):
    message: str
    message_type: str  # 'text', 'voice', 'image'

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: UUID
    user_id: UUID
    response: Optional[str] = None
    trust_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Image Analysis schemas
class ImageAnalysisBase(BaseModel):
    analysis_type: str  # 'crop', 'pest', 'disease', 'soil'

class ImageAnalysisCreate(ImageAnalysisBase):
    pass

class ImageAnalysis(ImageAnalysisBase):
    id: UUID
    user_id: UUID
    image_path: str
    results: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    recommendations: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Q&A Repository schemas
class QARepositoryBase(BaseModel):
    question: str
    answer: str
    crop_type: Optional[str] = None
    category: Optional[str] = None
    language: str = "malayalam"

class QARepositoryCreate(QARepositoryBase):
    pass

class QARepository(QARepositoryBase):
    id: UUID
    upvotes: int
    downvotes: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class QASearchResult(QARepository):
    similarity_score: Optional[float] = None


# Group Chat schemas
class GroupChatBase(BaseModel):
    name: str
    description: Optional[str] = None
    crop_type: Optional[str] = None
    location: Optional[str] = None

class GroupChatCreate(GroupChatBase):
    pass

class GroupChat(GroupChatBase):
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class GroupMessageBase(BaseModel):
    message: str
    message_type: str = "text"

class GroupMessageCreate(GroupMessageBase):
    group_id: UUID

class GroupMessage(GroupMessageBase):
    id: UUID
    group_id: UUID
    user_id: UUID
    created_at: datetime
    user: User
    
    class Config:
        from_attributes = True


# Retailer schemas
class RetailerBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    latitude: float
    longitude: float
    services: Optional[List[str]] = None

class RetailerCreate(RetailerBase):
    pass

class Retailer(RetailerBase):
    id: UUID
    rating: float
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class RetailerWithDistance(Retailer):
    distance: Optional[float] = None  # Distance in km