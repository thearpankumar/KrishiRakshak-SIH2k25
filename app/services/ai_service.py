import openai
from typing import Optional, Dict, Any, List
from ..core.config import settings
from ..models.database import User, UserProfile
import json
import asyncio
import base64
from .vector_service import vector_service

class AIService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def process_chat_message(
        self, 
        message: str, 
        message_type: str, 
        user: User,
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """Process chat message and return AI response."""
        
        # Build context for AI
        context = await self._build_user_context(user, user_profile)
        
        # Create system prompt based on user's preferred language
        language = user_profile.preferred_language if user_profile else "malayalam"
        system_prompt = self._get_system_prompt(language)
        
        try:
            if message_type == "text":
                response = await self._process_text_message(message, context, system_prompt, user_profile)
            elif message_type == "voice":
                # For now, treat voice as text (would need speech-to-text integration)
                response = await self._process_text_message(message, context, system_prompt, user_profile)
            elif message_type == "image":
                response = await self._process_image_message(message, context, system_prompt)
            else:
                raise ValueError(f"Unsupported message type: {message_type}")
            
            # Calculate trust score based on response confidence
            trust_score = self._calculate_trust_score(response.get("confidence", 0.8))
            
            return {
                "response": response["content"],
                "trust_score": trust_score,
                "tips": response.get("tips", []),
                "recommendations": response.get("recommendations", []),
                "similar_questions": response.get("similar_questions", [])
            }
            
        except Exception as e:
            return {
                "response": self._get_error_message(str(e), language),
                "trust_score": 0.0,
                "tips": [],
                "recommendations": [],
                "similar_questions": []
            }
    
    async def _process_text_message(
        self, 
        message: str, 
        context: str, 
        system_prompt: str,
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """Process text message using OpenAI with vector search enhancement."""
        
        # First, try to find similar questions in the knowledge base
        similar_questions = []
        try:
            crop_type = None
            if user_profile and user_profile.crops_grown:
                crop_type = user_profile.crops_grown[0] if user_profile.crops_grown else None
            
            language = user_profile.preferred_language if user_profile else "malayalam"
            
            similar_questions = await vector_service.search_similar_questions(
                query=message,
                crop_type=crop_type,
                language=language,
                limit=3,
                similarity_threshold=0.7
            )
        except Exception as e:
            print(f"Vector search failed: {e}")
        
        # Enhance context with similar Q&A if found
        enhanced_context = context
        if similar_questions:
            qa_context = "\n\nRelated Q&A from knowledge base:\n"
            for i, qa in enumerate(similar_questions[:2], 1):
                qa_context += f"{i}. Q: {qa['question']}\n   A: {qa['answer'][:200]}...\n"
            enhanced_context += qa_context
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {enhanced_context}\n\nQuestion: {message}"}
        ]
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        
        return {
            "content": content,
            "confidence": 0.85,  # Default confidence for text responses
            "tips": self._extract_tips_from_response(content),
            "recommendations": self._extract_recommendations_from_response(content),
            "similar_questions": similar_questions[:2]  # Return top 2 similar questions
        }
    
    async def _process_image_message(
        self, 
        image_path: str, 
        context: str, 
        system_prompt: str
    ) -> Dict[str, Any]:
        """Process image message using OpenAI Vision API."""
        
        try:
            # Read and encode image to base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            messages = [
                {
                    "role": "system",
                    "content": system_prompt + "\n\nAnalyze the provided image and give detailed agricultural advice."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Context: {context}\n\nPlease analyze this agricultural image and provide detailed insights and recommendations."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            return {
                "content": content,
                "confidence": 0.8,  # Good confidence for vision analysis
                "tips": self._extract_tips_from_response(content),
                "recommendations": self._extract_recommendations_from_response(content)
            }
            
        except Exception as e:
            return {
                "content": f"Unable to analyze the image at this time. Error: {str(e)}",
                "confidence": 0.0,
                "tips": [],
                "recommendations": []
            }
    
    async def _build_user_context(
        self, 
        user: User, 
        user_profile: Optional[UserProfile] = None
    ) -> str:
        """Build context string for AI based on user information."""
        
        context_parts = []
        
        # User location context
        if user.location:
            context_parts.append(f"User is located in: {user.location}")
        
        # User profile context
        if user_profile:
            if user_profile.crops_grown:
                crops = ", ".join(user_profile.crops_grown)
                context_parts.append(f"User grows these crops: {crops}")
            
            if user_profile.farm_size:
                context_parts.append(f"Farm size: {user_profile.farm_size} acres")
            
            if user_profile.farming_experience:
                context_parts.append(f"Farming experience: {user_profile.farming_experience} years")
        
        return ". ".join(context_parts) if context_parts else "No additional context available."
    
    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt based on user's preferred language."""
        
        prompts = {
            "malayalam": """You are a knowledgeable agricultural advisor specifically for farmers in Kerala, India. 
            Respond in Malayalam language. Provide practical, locally relevant farming advice considering Kerala's climate, 
            soil conditions, and traditional farming practices. Include seasonal recommendations, pest management, 
            and sustainable farming techniques. Be concise but helpful.""",
            
            "english": """You are a knowledgeable agricultural advisor for farmers in Kerala, India. 
            Provide practical, locally relevant farming advice considering Kerala's tropical climate, 
            soil conditions, and agricultural practices. Include seasonal recommendations, pest management, 
            and sustainable farming techniques. Be concise but helpful.""",
            
            "hindi": """आप केरल, भारत के किसानों के लिए एक जानकार कृषि सलाहकार हैं। 
            हिंदी में जवाब दें। केरल की जलवायु, मिट्टी की स्थिति और पारंपरिक खेती की प्रथाओं को ध्यान में रखते हुए 
            व्यावहारिक, स्थानीय रूप से प्रासंगिक कृषि सलाह प्रदान करें।"""
        }
        
        return prompts.get(language.lower(), prompts["english"])
    
    def _get_error_message(self, error: str, language: str) -> str:
        """Get error message in user's preferred language."""
        
        error_messages = {
            "malayalam": "ക്ഷമിക്കണം, ഇപ്പോൾ നിങ്ങളുടെ ചോദ്യത്തിന് ഉത്തരം നൽകാൻ കഴിയുന്നില്ല. ദയവായി പിന്നീട് വീണ്ടും ശ്രമിക്കുക.",
            "english": "Sorry, I'm unable to answer your question right now. Please try again later.",
            "hindi": "क्षमा करें, अभी मैं आपके प्रश्न का उत्तर देने में असमर्थ हूं। कृपया बाद में फिर से कोशिश करें।"
        }
        
        return error_messages.get(language.lower(), error_messages["english"])
    
    def _calculate_trust_score(self, confidence: float) -> float:
        """Calculate trust score based on AI confidence and other factors."""
        # Simple trust score calculation
        # In production, this could be more sophisticated
        return min(confidence * 0.95, 0.95)  # Cap at 95%
    
    def _extract_tips_from_response(self, content: str) -> List[str]:
        """Extract actionable tips from AI response."""
        # Simple extraction - in production, this could be more sophisticated
        tips = []
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['tip:', 'suggestion:', 'recommend:', 'try:']):
                tips.append(line.strip())
        return tips[:3]  # Return max 3 tips
    
    def _extract_recommendations_from_response(self, content: str) -> List[str]:
        """Extract recommendations from AI response."""
        # Simple extraction - in production, this could be more sophisticated
        recommendations = []
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['should', 'must', 'important', 'advised']):
                recommendations.append(line.strip())
        return recommendations[:2]  # Return max 2 recommendations

# Global AI service instance
ai_service = AIService()