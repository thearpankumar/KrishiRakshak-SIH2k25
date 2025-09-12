import openai
import base64
from typing import Dict, Any, List
from PIL import Image, ImageEnhance
import io
import os

from ..core.config import settings
from ..models.database import User


class ImageService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def analyze_image(
        self, 
        image_path: str, 
        analysis_type: str, 
        user: User
    ) -> Dict[str, Any]:
        """Analyze image using OpenAI Vision API."""
        
        try:
            # Prepare image for analysis
            processed_image_b64 = await self._prepare_image_for_analysis(image_path)
            
            # Get appropriate prompt based on analysis type
            system_prompt = self._get_analysis_prompt(analysis_type, user)
            
            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": f"Please analyze this image for {analysis_type} identification and provide detailed insights."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{processed_image_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            # Parse and structure the response
            analysis_result = self._parse_analysis_response(content, analysis_type)
            
            return analysis_result
            
        except Exception as e:
            # Return error analysis
            return {
                "results": {
                    "error": str(e),
                    "analysis_type": analysis_type
                },
                "confidence_score": 0.0,
                "recommendations": "Unable to analyze image. Please try again with a clearer image."
            }
    
    async def _prepare_image_for_analysis(self, image_path: str) -> str:
        """Prepare and optimize image for analysis."""
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (OpenAI has size limits)
                max_size = 1024
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Enhance image quality
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.2)
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
                
        except Exception as e:
            raise Exception(f"Image processing failed: {str(e)}")
    
    def _get_analysis_prompt(self, analysis_type: str, user: User) -> str:
        """Get appropriate system prompt based on analysis type."""
        
        base_context = f"""You are an expert agricultural advisor specializing in {analysis_type} analysis for farmers in Kerala, India. 
        Analyze the provided image and give practical, actionable advice suitable for Kerala's tropical climate and farming conditions."""
        
        prompts = {
            "crop": base_context + """
            For crop identification:
            1. Identify the crop type and variety if possible
            2. Assess the growth stage and health condition
            3. Note any visible issues (nutrient deficiencies, diseases, pests)
            4. Provide care recommendations specific to Kerala's climate
            5. Suggest optimal harvesting time if applicable
            6. Rate your confidence level (0.0 to 1.0)
            
            Format your response with clear sections: CROP_TYPE, GROWTH_STAGE, HEALTH_STATUS, ISSUES, RECOMMENDATIONS.""",
            
            "pest": base_context + """
            For pest identification:
            1. Identify any visible pests (insects, mites, etc.)
            2. Assess the severity of infestation
            3. Identify damage patterns and affected plant parts
            4. Recommend organic and chemical control methods suitable for Kerala
            5. Suggest preventive measures
            6. Provide timeline for treatment effectiveness
            
            Format your response with clear sections: PEST_TYPE, SEVERITY, DAMAGE_ASSESSMENT, TREATMENT_OPTIONS, PREVENTION.""",
            
            "disease": base_context + """
            For disease identification:
            1. Identify the disease based on symptoms visible in the image
            2. Assess disease severity and spread potential
            3. Identify the pathogen type (fungal, bacterial, viral)
            4. Recommend treatment methods suitable for Kerala's humid climate
            5. Provide preventive measures to avoid recurrence
            6. Suggest quarantine measures if needed
            
            Format your response with clear sections: DISEASE_NAME, PATHOGEN_TYPE, SEVERITY, SYMPTOMS, TREATMENT, PREVENTION.""",
            
            "soil": base_context + """
            For soil analysis:
            1. Assess soil color, texture, and visible composition
            2. Identify any visible issues (erosion, waterlogging, contamination)
            3. Estimate soil type (clay, sandy, loamy) based on appearance
            4. Suggest soil improvement methods for Kerala conditions
            5. Recommend suitable crops for this soil type
            6. Advise on drainage and water management
            
            Format your response with clear sections: SOIL_TYPE, TEXTURE, VISIBLE_ISSUES, IMPROVEMENT_METHODS, SUITABLE_CROPS."""
        }
        
        return prompts.get(analysis_type, prompts["crop"])
    
    def _parse_analysis_response(self, content: str, analysis_type: str) -> Dict[str, Any]:
        """Parse and structure the AI response."""
        
        try:
            # Extract confidence score from content if mentioned
            confidence_score = 0.8  # Default confidence
            
            if "confidence" in content.lower():
                # Try to extract numerical confidence
                import re
                confidence_match = re.search(r'confidence[:\s]*(\d+\.?\d*)%?', content.lower())
                if confidence_match:
                    confidence_value = float(confidence_match.group(1))
                    if confidence_value <= 1.0:
                        confidence_score = confidence_value
                    else:
                        confidence_score = confidence_value / 100.0
            
            # Structure results based on analysis type
            structured_results = {
                "analysis_type": analysis_type,
                "full_analysis": content,
                "key_findings": self._extract_key_findings(content),
                "detected_issues": self._extract_issues(content),
                "confidence_level": confidence_score
            }
            
            # Extract recommendations
            recommendations = self._extract_recommendations(content)
            
            return {
                "results": structured_results,
                "confidence_score": confidence_score,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "results": {
                    "analysis_type": analysis_type,
                    "full_analysis": content,
                    "parsing_error": str(e)
                },
                "confidence_score": 0.6,
                "recommendations": "Please review the full analysis for detailed recommendations."
            }
    
    def _extract_key_findings(self, content: str) -> List[str]:
        """Extract key findings from analysis content."""
        
        key_sections = [
            "CROP_TYPE", "PEST_TYPE", "DISEASE_NAME", "SOIL_TYPE",
            "GROWTH_STAGE", "SEVERITY", "HEALTH_STATUS", "TEXTURE"
        ]
        
        findings = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            for section in key_sections:
                if section.lower() in line.lower() and ':' in line:
                    findings.append(line)
                    break
        
        # Fallback: extract first few meaningful lines
        if not findings:
            for line in lines[:5]:
                line = line.strip()
                if len(line) > 20 and not line.startswith(('1.', '2.', '3.')):
                    findings.append(line)
        
        return findings[:5]  # Limit to 5 key findings
    
    def _extract_issues(self, content: str) -> List[str]:
        """Extract identified issues from content."""
        
        issue_keywords = [
            "deficiency", "disease", "pest", "damage", "problem", "issue",
            "infection", "infestation", "symptom", "affected"
        ]
        
        issues = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in issue_keywords):
                if len(line) > 15:
                    issues.append(line)
        
        return issues[:3]  # Limit to 3 main issues
    
    def _extract_recommendations(self, content: str) -> str:
        """Extract recommendations from analysis content."""
        
        recommendation_sections = [
            "RECOMMENDATIONS", "TREATMENT", "PREVENTION", 
            "IMPROVEMENT_METHODS", "TREATMENT_OPTIONS"
        ]
        
        lines = content.split('\n')
        recommendations = []
        capture = False
        
        for line in lines:
            line = line.strip()
            
            # Check if we hit a recommendation section
            if any(section in line.upper() for section in recommendation_sections):
                capture = True
                if ':' in line:
                    line = line.split(':', 1)[1].strip()
                if line:
                    recommendations.append(line)
                continue
            
            # If we're capturing and hit another section, stop
            if capture and any(section in line.upper() for section in ["CROP_TYPE", "PEST_TYPE", "DISEASE_NAME", "SOIL_TYPE"]):
                break
            
            # Continue capturing recommendation content
            if capture and line and not line.startswith(('Format', 'Note:')):
                recommendations.append(line)
        
        # Fallback: look for general recommendation patterns
        if not recommendations:
            for line in lines:
                line = line.strip()
                if any(word in line.lower() for word in ['recommend', 'suggest', 'should', 'apply', 'use']):
                    recommendations.append(line)
        
        return '\n'.join(recommendations[:10])  # Limit length


# Global image service instance
image_service = ImageService()