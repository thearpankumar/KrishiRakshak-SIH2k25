from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, text, String
from typing import List, Optional
import math

from ..core.database import get_session
from ..core.dependencies import get_current_active_user
from ..models.database import User, Retailer
from ..models.schemas import (
    Retailer as RetailerSchema,
    RetailerCreate,
    RetailerWithDistance
)

router = APIRouter()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return round(distance, 2)

@router.post("/retailers", response_model=RetailerSchema)
async def create_retailer(
    retailer_data: RetailerCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new retailer entry."""
    
    db_retailer = Retailer(
        name=retailer_data.name,
        contact_person=retailer_data.contact_person,
        phone_number=retailer_data.phone_number,
        email=retailer_data.email,
        address=retailer_data.address,
        latitude=retailer_data.latitude,
        longitude=retailer_data.longitude,
        services=retailer_data.services
    )
    
    session.add(db_retailer)
    await session.commit()
    await session.refresh(db_retailer)
    
    return db_retailer

@router.get("/retailers/nearby", response_model=List[RetailerWithDistance])
async def get_nearby_retailers(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, gt=0, le=100),
    services: Optional[List[str]] = Query(None),
    is_verified: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get nearby retailers based on location."""
    
    # Use Python-based distance calculation for reliable results
    result = await session.execute(select(Retailer))
    all_retailers = result.scalars().all()

    retailers_with_distance = []

    for retailer in all_retailers:
        # Apply filters first
        if is_verified is not None and retailer.is_verified != is_verified:
            continue

        if services and not (retailer.services and any(service in retailer.services for service in services)):
            continue

        # Skip retailers without valid coordinates
        if retailer.latitude is None or retailer.longitude is None:
            continue

        distance = calculate_distance(
            latitude, longitude,
            retailer.latitude, retailer.longitude
        )

        if distance <= radius_km:
            retailer_dict = {
                "id": retailer.id,
                "name": retailer.name,
                "contact_person": retailer.contact_person,
                "phone_number": retailer.phone_number,
                "email": retailer.email,
                "address": retailer.address,
                "latitude": retailer.latitude,
                "longitude": retailer.longitude,
                "services": retailer.services,
                "rating": retailer.rating,
                "is_verified": retailer.is_verified,
                "created_at": retailer.created_at,
                "updated_at": retailer.updated_at,
                "distance": distance
            }
            retailers_with_distance.append(RetailerWithDistance(**retailer_dict))

    # Sort by distance (primary) and then by ID (secondary) for stable sorting
    retailers_with_distance.sort(key=lambda x: (x.distance if x.distance is not None else float('inf'), str(x.id)))
    retailers = retailers_with_distance[:limit]

    # Debug: Print distances for troubleshooting
    distances = [r.distance for r in retailers]
    print(f"🔍 DEBUG: Returning distances in order: {distances}")

    return retailers

@router.get("/retailers", response_model=List[RetailerSchema])
async def get_retailers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_verified: Optional[bool] = Query(None),
    services: Optional[List[str]] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Get list of retailers with optional filtering."""
    
    query = select(Retailer)
    
    # Apply filters
    if is_verified is not None:
        query = query.where(Retailer.is_verified == is_verified)
    
    # Filter by services - this would need to be adapted based on how services are stored
    if services:
        # Use simple approach - check if the service string appears in the JSON array
        service_conditions = []
        for service in services:
            # Use LIKE operator to check if service is contained in the JSON text
            service_conditions.append(
                Retailer.services.cast(String).contains(f'"{service}"')
            )
        if service_conditions:
            from sqlalchemy import or_
            query = query.where(or_(*service_conditions))
    
    # Order by rating and creation date
    query = query.order_by(desc(Retailer.rating), desc(Retailer.created_at))
    query = query.offset(skip).limit(limit)
    
    result = await session.execute(query)
    retailers = result.scalars().all()
    
    return retailers

@router.get("/retailers/{retailer_id}", response_model=RetailerSchema)
async def get_retailer(
    retailer_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific retailer by ID."""
    
    result = await session.execute(
        select(Retailer).where(Retailer.id == retailer_id)
    )
    
    retailer = result.scalar_one_or_none()
    if not retailer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found"
        )
    
    return retailer

@router.put("/retailers/{retailer_id}", response_model=RetailerSchema)
async def update_retailer(
    retailer_id: str,
    retailer_update: RetailerCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Update a retailer entry."""
    
    result = await session.execute(
        select(Retailer).where(Retailer.id == retailer_id)
    )
    
    retailer = result.scalar_one_or_none()
    if not retailer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found"
        )
    
    # Update fields
    retailer.name = retailer_update.name
    retailer.contact_person = retailer_update.contact_person
    retailer.phone_number = retailer_update.phone_number
    retailer.email = retailer_update.email
    retailer.address = retailer_update.address
    retailer.latitude = retailer_update.latitude
    retailer.longitude = retailer_update.longitude
    retailer.services = retailer_update.services
    
    await session.commit()
    await session.refresh(retailer)
    
    return retailer

@router.delete("/retailers/{retailer_id}")
async def delete_retailer(
    retailer_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a retailer entry."""
    
    result = await session.execute(
        select(Retailer).where(Retailer.id == retailer_id)
    )
    
    retailer = result.scalar_one_or_none()
    if not retailer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found"
        )
    
    await session.delete(retailer)
    await session.commit()
    
    return {"message": "Retailer deleted successfully"}

@router.post("/retailers/{retailer_id}/rate")
async def rate_retailer(
    retailer_id: str,
    rating: float = Query(..., ge=1.0, le=5.0),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Rate a retailer (simplified version - in production, you'd track individual ratings)."""
    
    result = await session.execute(
        select(Retailer).where(Retailer.id == retailer_id)
    )
    
    retailer = result.scalar_one_or_none()
    if not retailer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found"
        )
    
    # Simple rating update (in production, you'd maintain individual ratings and calculate average)
    if retailer.rating == 0.0:
        retailer.rating = rating
    else:
        # Simple average - in production, you'd have a proper rating system
        retailer.rating = round((retailer.rating + rating) / 2, 2)
    
    await session.commit()
    
    return {
        "message": "Rating submitted successfully",
        "new_rating": retailer.rating
    }

@router.get("/services/list")
async def get_available_services(
    session: AsyncSession = Depends(get_session)
):
    """Get list of available services from all retailers."""
    
    result = await session.execute(
        select(Retailer.services).where(Retailer.services.is_not(None))
    )
    
    all_services = result.scalars().all()
    
    # Flatten and count services
    service_counts = {}
    for services_list in all_services:
        if services_list:
            for service in services_list:
                service_counts[service] = service_counts.get(service, 0) + 1
    
    # Sort by popularity
    sorted_services = sorted(
        service_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return [
        {"name": service, "count": count}
        for service, count in sorted_services
    ]

@router.get("/area-coverage")
async def get_area_coverage(
    session: AsyncSession = Depends(get_session)
):
    """Get geographical coverage of retailers."""
    
    result = await session.execute(
        select(
            func.min(Retailer.latitude).label('min_lat'),
            func.max(Retailer.latitude).label('max_lat'),
            func.min(Retailer.longitude).label('min_lng'),
            func.max(Retailer.longitude).label('max_lng'),
            func.count(Retailer.id).label('total_retailers')
        )
    )
    
    coverage = result.first()
    
    return {
        "bounds": {
            "min_latitude": float(coverage.min_lat) if coverage.min_lat else None,
            "max_latitude": float(coverage.max_lat) if coverage.max_lat else None,
            "min_longitude": float(coverage.min_lng) if coverage.min_lng else None,
            "max_longitude": float(coverage.max_lng) if coverage.max_lng else None
        },
        "total_retailers": coverage.total_retailers
    }

@router.get("/retailers/{retailer_id}/distance")
async def get_distance_to_retailer(
    retailer_id: str,
    user_latitude: float = Query(..., ge=-90, le=90),
    user_longitude: float = Query(..., ge=-180, le=180),
    session: AsyncSession = Depends(get_session)
):
    """Calculate distance from user location to a specific retailer."""
    
    result = await session.execute(
        select(Retailer).where(Retailer.id == retailer_id)
    )
    
    retailer = result.scalar_one_or_none()
    if not retailer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found"
        )
    
    distance = calculate_distance(
        user_latitude, user_longitude,
        retailer.latitude, retailer.longitude
    )
    
    return {
        "retailer_id": retailer_id,
        "retailer_name": retailer.name,
        "distance_km": distance,
        "retailer_location": {
            "latitude": retailer.latitude,
            "longitude": retailer.longitude,
            "address": retailer.address
        }
    }

@router.get("/search-by-location")
async def search_by_location_name(
    location_name: str = Query(..., min_length=2),
    radius_km: float = Query(50, gt=0, le=200),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session)
):
    """Search retailers by location name (address matching)."""
    
    # Simple text search in address field
    result = await session.execute(
        select(Retailer)
        .where(
            func.lower(Retailer.address).contains(location_name.lower())
        )
        .order_by(desc(Retailer.rating))
        .limit(limit)
    )
    
    retailers = result.scalars().all()
    
    return {
        "location_query": location_name,
        "retailers_found": len(retailers),
        "retailers": retailers
    }