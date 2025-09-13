from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_, and_
from typing import List, Optional
import uuid

from ..core.database import get_session
from ..core.dependencies import get_current_active_user
from ..models.database import User, QARepository
from ..models.schemas import (
    QARepository as QARepositorySchema,
    QARepositoryCreate,
    QASearchResult
)
from ..services.vector_service import vector_service
from ..services.ai_service import ai_service

router = APIRouter()

@router.post("/", response_model=QARepositorySchema)
async def create_qa_entry(
    qa_data: QARepositoryCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new Q&A entry in the knowledge repository."""
    
    # Create database entry
    db_qa = QARepository(
        question=qa_data.question,
        answer=qa_data.answer,
        crop_type=qa_data.crop_type,
        category=qa_data.category,
        language=qa_data.language
    )
    
    session.add(db_qa)
    await session.commit()
    await session.refresh(db_qa)
    
    # Add to vector database for semantic search
    await vector_service.add_qa_to_vector_db(
        qa_id=str(db_qa.id),
        question=qa_data.question,
        answer=qa_data.answer,
        crop_type=qa_data.crop_type,
        category=qa_data.category,
        language=qa_data.language
    )
    
    return db_qa

@router.get("/search", response_model=List[QASearchResult])
async def search_knowledge(
    query: str = Query(..., min_length=3),
    crop_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query("english"),
    limit: int = Query(10, ge=1, le=50),
    use_vector_search: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Search the knowledge repository using both vector and traditional search."""
    
    results = []
    
    if use_vector_search:
        # Try vector search first
        vector_results = await vector_service.search_similar_questions(
            query=query,
            limit=limit,
            crop_type=crop_type,
            category=category,
            language=language,
            similarity_threshold=0.6
        )
        
        # Convert vector results to schema format
        for result in vector_results:
            # Get full record from database to ensure data consistency
            db_result = await session.execute(
                select(QARepository).where(QARepository.id == result["qa_id"])
            )
            qa_record = db_result.scalar_one_or_none()
            
            if qa_record:
                qa_dict = {
                    "id": qa_record.id,
                    "question": qa_record.question,
                    "answer": qa_record.answer,
                    "crop_type": qa_record.crop_type,
                    "category": qa_record.category,
                    "language": qa_record.language,
                    "upvotes": qa_record.upvotes,
                    "downvotes": qa_record.downvotes,
                    "created_at": qa_record.created_at,
                    "updated_at": qa_record.updated_at,
                    "similarity_score": result["similarity_score"]
                }
                results.append(QASearchResult(**qa_dict))
    
    # If vector search didn't return enough results, supplement with traditional search
    if len(results) < limit // 2:
        traditional_results = await _traditional_search(
            session=session,
            query=query,
            crop_type=crop_type,
            category=category,
            language=language,
            limit=limit - len(results)
        )
        
        # Add traditional results that aren't already in vector results
        existing_ids = {str(result.id) for result in results}
        for result in traditional_results:
            if str(result.id) not in existing_ids:
                result.similarity_score = 0.5  # Default score for traditional search
                results.append(result)
    
    return results[:limit]

async def _traditional_search(
    session: AsyncSession,
    query: str,
    crop_type: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 10
) -> List[QASearchResult]:
    """Traditional keyword-based search fallback."""
    
    # Build search conditions
    search_conditions = []
    
    # Text search in question and answer
    search_terms = query.lower().split()
    for term in search_terms:
        term_condition = or_(
            func.lower(QARepository.question).contains(term),
            func.lower(QARepository.answer).contains(term)
        )
        search_conditions.append(term_condition)
    
    # Filter conditions
    filter_conditions = []
    if crop_type:
        filter_conditions.append(QARepository.crop_type == crop_type)
    if category:
        filter_conditions.append(QARepository.category == category)
    if language:
        filter_conditions.append(QARepository.language == language)
    
    # Combine all conditions
    all_conditions = search_conditions + filter_conditions
    
    if all_conditions:
        query_condition = and_(*all_conditions) if len(all_conditions) > 1 else all_conditions[0]
    else:
        # No search terms, return most popular entries
        query_condition = True
    
    # Execute search query
    result = await session.execute(
        select(QARepository)
        .where(query_condition)
        .order_by(desc(QARepository.upvotes), desc(QARepository.created_at))
        .limit(limit)
    )
    
    qa_records = result.scalars().all()
    
    # Convert to search result format
    search_results = []
    for qa in qa_records:
        qa_dict = {
            "id": qa.id,
            "question": qa.question,
            "answer": qa.answer,
            "crop_type": qa.crop_type,
            "category": qa.category,
            "language": qa.language,
            "upvotes": qa.upvotes,
            "downvotes": qa.downvotes,
            "created_at": qa.created_at,
            "updated_at": qa.updated_at
        }
        search_results.append(QASearchResult(**qa_dict))
    
    return search_results

@router.get("/", response_model=List[QARepositorySchema])
async def get_qa_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    crop_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Get Q&A entries with optional filtering."""
    
    query = select(QARepository)
    
    # Apply filters
    if crop_type:
        query = query.where(QARepository.crop_type == crop_type)
    if category:
        query = query.where(QARepository.category == category)
    if language:
        query = query.where(QARepository.language == language)
    
    # Order by popularity and recency
    query = query.order_by(desc(QARepository.upvotes), desc(QARepository.created_at))
    query = query.offset(skip).limit(limit)
    
    result = await session.execute(query)
    qa_entries = result.scalars().all()
    
    return qa_entries

@router.get("/popular", response_model=List[QARepositorySchema])
async def get_popular_questions(
    limit: int = Query(20, ge=1, le=100),
    crop_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Get popular Q&A entries sorted by upvotes."""

    query = select(QARepository)

    # Apply filters
    if crop_type:
        query = query.where(QARepository.crop_type == crop_type)
    if category:
        query = query.where(QARepository.category == category)
    if language:
        query = query.where(QARepository.language == language)

    # Order by popularity (upvotes first, then by creation date)
    query = query.order_by(
        desc(QARepository.upvotes),
        desc(QARepository.created_at)
    ).limit(limit)

    result = await session.execute(query)
    popular_entries = result.scalars().all()

    return popular_entries

@router.get("/{qa_id}", response_model=QARepositorySchema)
async def get_qa_entry(
    qa_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific Q&A entry by ID."""
    
    result = await session.execute(
        select(QARepository).where(QARepository.id == qa_id)
    )
    
    qa_entry = result.scalar_one_or_none()
    if not qa_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Q&A entry not found"
        )
    
    return qa_entry

@router.put("/{qa_id}", response_model=QARepositorySchema)
async def update_qa_entry(
    qa_id: str,
    qa_update: QARepositoryCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Update a Q&A entry."""
    
    result = await session.execute(
        select(QARepository).where(QARepository.id == qa_id)
    )
    
    qa_entry = result.scalar_one_or_none()
    if not qa_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Q&A entry not found"
        )
    
    # Update fields
    qa_entry.question = qa_update.question
    qa_entry.answer = qa_update.answer
    qa_entry.crop_type = qa_update.crop_type
    qa_entry.category = qa_update.category
    qa_entry.language = qa_update.language
    
    await session.commit()
    await session.refresh(qa_entry)
    
    # Update vector database
    await vector_service.update_qa_in_vector_db(
        qa_id=str(qa_entry.id),
        question=qa_update.question,
        answer=qa_update.answer,
        crop_type=qa_update.crop_type,
        category=qa_update.category,
        language=qa_update.language
    )
    
    return qa_entry

@router.delete("/{qa_id}")
async def delete_qa_entry(
    qa_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a Q&A entry."""
    
    result = await session.execute(
        select(QARepository).where(QARepository.id == qa_id)
    )
    
    qa_entry = result.scalar_one_or_none()
    if not qa_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Q&A entry not found"
        )
    
    # Delete from database
    await session.delete(qa_entry)
    await session.commit()
    
    # Delete from vector database
    await vector_service.delete_qa_from_vector_db(qa_id)
    
    return {"message": "Q&A entry deleted successfully"}

@router.post("/{qa_id}/vote")
async def vote_qa_entry(
    qa_id: str,
    vote_type: str = Query(..., regex="^(upvote|downvote)$"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Vote on a Q&A entry (upvote or downvote)."""
    
    result = await session.execute(
        select(QARepository).where(QARepository.id == qa_id)
    )
    
    qa_entry = result.scalar_one_or_none()
    if not qa_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Q&A entry not found"
        )
    
    # Update vote count
    if vote_type == "upvote":
        qa_entry.upvotes += 1
    else:
        qa_entry.downvotes += 1
    
    await session.commit()
    
    return {
        "message": f"Successfully {vote_type}d",
        "upvotes": qa_entry.upvotes,
        "downvotes": qa_entry.downvotes
    }

@router.post("/ask-ai")
async def ask_ai_question(
    question: str = Query(..., min_length=10),
    crop_type: Optional[str] = Query(None),
    language: str = Query("english"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Ask a question to AI and optionally save to knowledge base."""
    
    # First, search existing knowledge base
    similar_entries = await vector_service.search_similar_questions(
        query=question,
        crop_type=crop_type,
        language=language,
        limit=3,
        similarity_threshold=0.8
    )
    
    # If we have very similar questions, return the best match
    if similar_entries and similar_entries[0]["similarity_score"] > 0.9:
        best_match = similar_entries[0]
        return {
            "answer": best_match["answer"],
            "source": "knowledge_base",
            "similarity_score": best_match["similarity_score"],
            "qa_id": best_match["qa_id"]
        }
    
    # Otherwise, get AI response
    ai_response = await ai_service.process_chat_message(
        message=question,
        message_type="text",
        user=current_user,
        user_profile=None  # Could get user profile if needed
    )
    
    # Optionally save high-quality responses to knowledge base
    if ai_response["trust_score"] > 0.8:
        new_qa = QARepository(
            question=question,
            answer=ai_response["response"],
            crop_type=crop_type,
            category="ai_generated",
            language=language
        )
        
        session.add(new_qa)
        await session.commit()
        await session.refresh(new_qa)
        
        # Add to vector database
        await vector_service.add_qa_to_vector_db(
            qa_id=str(new_qa.id),
            question=question,
            answer=ai_response["response"],
            crop_type=crop_type,
            category="ai_generated",
            language=language
        )
    
    return {
        "answer": ai_response["response"],
        "source": "ai_generated",
        "trust_score": ai_response["trust_score"],
        "similar_questions": similar_entries[:2] if similar_entries else []
    }

@router.get("/categories/list")
async def get_categories(
    session: AsyncSession = Depends(get_session)
):
    """Get list of available categories."""
    
    result = await session.execute(
        select(QARepository.category, func.count(QARepository.id).label('count'))
        .where(QARepository.category.is_not(None))
        .group_by(QARepository.category)
        .order_by(desc('count'))
    )
    
    categories = result.all()
    
    return [{"name": cat.category, "count": cat.count} for cat in categories]

@router.get("/crops/list")
async def get_crops(
    session: AsyncSession = Depends(get_session)
):
    """Get list of available crop types."""
    
    result = await session.execute(
        select(QARepository.crop_type, func.count(QARepository.id).label('count'))
        .where(QARepository.crop_type.is_not(None))
        .group_by(QARepository.crop_type)
        .order_by(desc('count'))
    )
    
    crops = result.all()
    
    return [{"name": crop.crop_type, "count": crop.count} for crop in crops]