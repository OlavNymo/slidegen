"""
Service for interacting with Google Gemini API.
"""

import base64
import os
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

from ..exceptions import APIError


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self, api_key: str):
        """Initialize the Gemini service with API key."""
        self.api_key = api_key
        self._setup_api()
    
    def _setup_api(self) -> None:
        """Setup Gemini API with the provided key."""
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            raise APIError(f"Failed to setup Gemini API: {str(e)}")
    
    def analyze_images(self, prompt: str, images: List[Dict[str, Any]]) -> str:
        """Analyze images using Gemini API."""
        try:
            model = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite", 
                google_api_key=self.api_key, 
                temperature=0.1
            )
            
            content_parts = [{"type": "text", "text": prompt}]
            
            for img in images:
                if os.path.exists(img["path"]):
                    with open(img["path"], "rb") as f:
                        image_bytes = f.read()
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"}
                    })
            
            message = HumanMessage(content=content_parts)
            response = model.invoke([message])
            return response.content
            
        except Exception as e:
            raise APIError(f"Failed to analyze images: {str(e)}")
    
    def generate_latex(self, prompt: str, images: List[Dict[str, Any]]) -> str:
        """Generate LaTeX content using Gemini API."""
        try:
            model = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite", 
                google_api_key=self.api_key, 
                temperature=0.1
            )
            
            content_parts = [{"type": "text", "text": prompt}]
            
            # Only send images that actually exist
            for img in images:
                if os.path.exists(img["path"]):
                    with open(img["path"], "rb") as f:
                        img_bytes = f.read()
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}"}
                    })
            
            message = HumanMessage(content=content_parts)
            response = model.invoke([message])
            return response.content
            
        except Exception as e:
            raise APIError(f"Failed to generate LaTeX: {str(e)}")
