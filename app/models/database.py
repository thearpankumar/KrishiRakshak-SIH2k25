from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True)
    location = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    chat_messages = relationship("ChatMessage", back_populates="user")
    image_analyses = relationship("ImageAnalysis", back_populates="user")
    user_profile = relationship("UserProfile", back_populates="user", uselist=False)
    notification_logs = relationship("NotificationLog", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    crop_types = Column(JSON)  # List of crops the farmer grows
    farm_size = Column(Float)  # Farm size in acres
    farming_experience = Column(Integer)  # Years of experience
    preferred_language = Column(String, default="malayalam")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_profile")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String, nullable=False)  # 'text', 'voice', 'image'
    response = Column(Text)
    trust_score = Column(Float)  # AI confidence/trust score
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")


class ImageAnalysis(Base):
    __tablename__ = "image_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    image_path = Column(String, nullable=False)
    analysis_type = Column(String, nullable=False)  # 'crop', 'pest', 'disease', 'soil'
    results = Column(JSON)  # Analysis results
    confidence_score = Column(Float)
    recommendations = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="image_analyses")


class QARepository(Base):
    __tablename__ = "qa_repository"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    crop_type = Column(String)  # Associated crop type
    category = Column(String)  # 'pest', 'disease', 'fertilizer', 'general'
    language = Column(String, default="malayalam")
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class GroupChat(Base):
    __tablename__ = "group_chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    crop_type = Column(String)  # Associated crop for focused discussions
    location = Column(String)  # Geographic focus
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    messages = relationship("GroupMessage", back_populates="group")


class GroupMessage(Base):
    __tablename__ = "group_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("group_chats.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String, default="text")  # 'text', 'image', 'file'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    group = relationship("GroupChat", back_populates="messages")
    user = relationship("User")


class Retailer(Base):
    __tablename__ = "retailers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    contact_person = Column(String)
    phone_number = Column(String)
    email = Column(String)
    address = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    services = Column(JSON)  # List of services/products offered
    rating = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# New models for N8N integration

class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    weather_condition = Column(String)
    wind_speed = Column(Float)
    agricultural_insights = Column(JSON)  # AI-generated farming insights
    alerts = Column(JSON)  # Weather alerts and warnings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commodity = Column(String, nullable=False)
    market_name = Column(String)
    location = Column(String)
    min_price = Column(Float)
    max_price = Column(Float)
    modal_price = Column(Float)
    price_unit = Column(String)  # per kg, per quintal, etc.
    arrival_date = Column(Date)
    source = Column(String)  # API source
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notification_type = Column(String, nullable=False)
    content = Column(JSON)  # Notification content and metadata
    delivery_channels = Column(JSON)  # push, sms, email, etc.
    delivery_status = Column(String, default="pending")  # pending, delivered, failed
    priority = Column(String, default="medium")  # low, medium, high, urgent
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="notification_logs")


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_name = Column(String, nullable=False)
    workflow_id = Column(String)  # N8N workflow ID
    trigger_data = Column(JSON)  # Data sent to trigger the workflow
    status = Column(String, default="triggered")  # triggered, running, completed, failed
    result_data = Column(JSON)  # Result data from workflow
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    execution_time = Column(Float)  # Execution time in seconds
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")


class ContentModerationLog(Base):
    __tablename__ = "content_moderation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(String, nullable=False)  # ID of the content being moderated
    content_type = Column(String, nullable=False)  # group_message, chat_message, user_profile
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_content = Column(Text)
    moderation_action = Column(String)  # approve, reject, review
    confidence_score = Column(Float)
    reasons = Column(JSON)  # Reasons for moderation decision
    reviewed_by_human = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")