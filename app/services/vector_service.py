from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import openai
from typing import List, Dict, Any, Optional
import uuid
import asyncio
from ..core.config import settings


class VectorService:
    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.qdrant_url)
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.collection_name = settings.qdrant_collection_name
        self._initialized = False
    
    async def initialize(self):
        """Initialize the vector database collection."""
        if self._initialized:
            return
            
        try:
            # Check if collection exists
            collections = await self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection with appropriate vector configuration
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI text-embedding-3-small dimensions
                        distance=Distance.COSINE,
                    ),
                )
                print(f"Created Qdrant collection: {self.collection_name}")
            
            self._initialized = True
            
        except Exception as e:
            print(f"Failed to initialize Qdrant collection: {e}")
            # Continue without vector search for now
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI."""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Failed to get embedding: {e}")
            return []
    
    async def add_qa_to_vector_db(
        self, 
        qa_id: str, 
        question: str, 
        answer: str, 
        crop_type: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "malayalam"
    ):
        """Add Q&A pair to vector database."""
        await self.initialize()
        
        try:
            # Create searchable text combining question and answer
            search_text = f"Question: {question}\nAnswer: {answer}"
            
            # Get embedding
            embedding = await self.get_embedding(search_text)
            if not embedding:
                return False
            
            # Create point for insertion
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "qa_id": qa_id,
                    "question": question,
                    "answer": answer,
                    "crop_type": crop_type,
                    "category": category,
                    "language": language,
                    "search_text": search_text
                }
            )
            
            # Insert into Qdrant
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to add Q&A to vector DB: {e}")
            return False
    
    async def search_similar_questions(
        self, 
        query: str, 
        limit: int = 5,
        crop_type: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar questions using vector similarity."""
        await self.initialize()
        
        try:
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            if not query_embedding:
                return []
            
            # Build filter conditions
            filter_conditions = []
            
            if crop_type:
                filter_conditions.append(
                    FieldCondition(key="crop_type", match=MatchValue(value=crop_type))
                )
            
            if category:
                filter_conditions.append(
                    FieldCondition(key="category", match=MatchValue(value=category))
                )
            
            if language:
                filter_conditions.append(
                    FieldCondition(key="language", match=MatchValue(value=language))
                )
            
            # Create filter object
            search_filter = None
            if filter_conditions:
                search_filter = Filter(must=filter_conditions)
            
            # Search in Qdrant
            search_results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=similarity_threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "qa_id": result.payload.get("qa_id"),
                    "question": result.payload.get("question"),
                    "answer": result.payload.get("answer"),
                    "crop_type": result.payload.get("crop_type"),
                    "category": result.payload.get("category"),
                    "language": result.payload.get("language"),
                    "similarity_score": result.score,
                    "vector_id": result.id
                })
            
            return results
            
        except Exception as e:
            print(f"Vector search failed: {e}")
            return []
    
    async def update_qa_in_vector_db(
        self, 
        qa_id: str, 
        question: str, 
        answer: str, 
        crop_type: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "malayalam"
    ):
        """Update Q&A pair in vector database."""
        await self.initialize()
        
        try:
            # First, find existing entries for this Q&A
            existing_points = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="qa_id", match=MatchValue(value=qa_id))]
                ),
                limit=10
            )
            
            # Delete existing entries
            if existing_points[0]:  # existing_points is (points, next_page_offset)
                point_ids = [point.id for point in existing_points[0]]
                await self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
            
            # Add updated entry
            return await self.add_qa_to_vector_db(
                qa_id=qa_id,
                question=question,
                answer=answer,
                crop_type=crop_type,
                category=category,
                language=language
            )
            
        except Exception as e:
            print(f"Failed to update Q&A in vector DB: {e}")
            return False
    
    async def delete_qa_from_vector_db(self, qa_id: str):
        """Delete Q&A pair from vector database."""
        await self.initialize()
        
        try:
            # Find and delete all points for this Q&A
            existing_points = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="qa_id", match=MatchValue(value=qa_id))]
                ),
                limit=10
            )
            
            if existing_points[0]:
                point_ids = [point.id for point in existing_points[0]]
                await self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
            
            return True
            
        except Exception as e:
            print(f"Failed to delete Q&A from vector DB: {e}")
            return False
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the vector collection."""
        await self.initialize()
        
        try:
            collection_info = await self.client.get_collection(self.collection_name)
            return {
                "status": collection_info.status,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def hybrid_search(
        self, 
        query: str, 
        fallback_keywords: List[str],
        limit: int = 5,
        **filters
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search: vector similarity + keyword fallback."""
        
        # Try vector search first
        vector_results = await self.search_similar_questions(
            query=query, 
            limit=limit, 
            **filters
        )
        
        # If vector search returns good results, use them
        if vector_results and len(vector_results) >= 2:
            return vector_results
        
        # Fallback to keyword-based search logic would go here
        # For now, return vector results even if limited
        return vector_results
    
    async def bulk_index_qa_data(self, qa_data: List[Dict[str, Any]]):
        """Bulk index Q&A data for initial setup."""
        await self.initialize()
        
        points = []
        for qa in qa_data:
            try:
                search_text = f"Question: {qa['question']}\nAnswer: {qa['answer']}"
                embedding = await self.get_embedding(search_text)
                
                if embedding:
                    point = PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            "qa_id": qa['id'],
                            "question": qa['question'],
                            "answer": qa['answer'],
                            "crop_type": qa.get('crop_type'),
                            "category": qa.get('category'),
                            "language": qa.get('language', 'malayalam'),
                            "search_text": search_text
                        }
                    )
                    points.append(point)
                
                # Process in batches to avoid overwhelming the API
                if len(points) >= 10:
                    await self.client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    points = []
                    await asyncio.sleep(0.1)  # Small delay between batches
                    
            except Exception as e:
                print(f"Failed to process Q&A {qa.get('id', 'unknown')}: {e}")
                continue
        
        # Insert remaining points
        if points:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        
        return len(qa_data)


# Global vector service instance
vector_service = VectorService()