import openai
from typing import Optional, Dict, Any, List
from ..core.config import settings
from ..models.database import User, UserProfile
import json
import asyncio

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
                response = await self._process_text_message(message, context, system_prompt)
            elif message_type == "voice":
                # For now, treat voice as text (would need speech-to-text integration)
                response = await self._process_text_message(message, context, system_prompt)
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
                "recommendations": response.get("recommendations", [])
            }
            
        except Exception as e:
            return {
                "response": self._get_error_message(str(e), language),
                "trust_score": 0.0,
                "tips": [],
                "recommendations": []
            }
    
    async def _process_text_message(
        self, 
        message: str, 
        context: str, 
        system_prompt: str
    ) -> Dict[str, Any]:
        """Process text message using OpenAI."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {message}"}
        ]
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        return {
            "content": content,
            "confidence": 0.85,  # Default confidence for text responses
            "tips": self._extract_tips_from_response(content),
            "recommendations": self._extract_recommendations_from_response(content)
        }
    
    async def _process_image_message(
        self, 
        image_path: str, 
        context: str, 
        system_prompt: str
    ) -> Dict[str, Any]:
        """Process image message using OpenAI Vision."""
        
        # For now, return a placeholder response
        # In production, you would integrate with OpenAI Vision API
        return {
            "content": "Image analysis feature will be implemented with OpenAI Vision API.",
            "confidence": 0.5,
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