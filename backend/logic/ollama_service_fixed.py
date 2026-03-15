"""
Ollama Service for Local AI Question Generation
Simple integration with Ollama for dynamic question generation
"""

import requests
import json
import random
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OllamaService:
    """Ollama service for AI question generation"""
    
    def __init__(self):
        self.api_url = "http://localhost:11434/api/generate"
        self.models_url = "http://localhost:11434/api/tags"
        self.available_models = []
        self.default_model = "phi3"  # Small, fast model
        
        # Check if Ollama is available
        self.is_available = self._check_availability()
        
        if self.is_available:
            self._load_available_models()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(self.models_url, timeout=3)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    def _load_available_models(self):
        """Load available models from Ollama"""
        try:
            response = requests.get(self.models_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model['name'] for model in data.get('models', [])]
                logger.info(f"🤖 Available Ollama models: {self.available_models}")
                
                # Set default model to first available if phi3 not found
                if self.default_model not in self.available_models and self.available_models:
                    self.default_model = self.available_models[0]
                    logger.info(f"Using default model: {self.default_model}")
        except Exception as e:
            logger.warning(f"Failed to load Ollama models: {e}")
    
    def generate_question(self, song_data: List[Dict[str, Any]], asked_questions: set) -> Optional[Dict[str, Any]]:
        """Generate a question using Ollama"""
        if not self.is_available or not self.available_models:
            return None
        
        try:
            # Get sample songs for context
            sample_songs = random.sample(song_data, min(3, len(song_data)))
            
            # Extract some attributes for the prompt
            sample_artists = []
            sample_genres = []
            for song in sample_songs:
                if 'artists' in song and song['artists']:
                    sample_artists.extend(song['artists'][:2])
                if 'genres' in song and song['genres']:
                    sample_genres.extend(song['genres'][:2])
            
            # Create prompt
            prompt = f"""You are a friendly music guessing game host. Generate a natural, conversational question about a song.

Here are some example artists: {', '.join(set(sample_artists[:5]))}
Here are some example genres: {', '.join(set(sample_genres[:5]))}

Generate a question that a normal person could answer about a song.
Make it conversational and engaging. Don't be too technical.
Keep it under 20 words.

Examples:
- Would you say this has a pop feel?
- Does this sound like something from the 2010s?
- Is this more of a chill vibe?
- Would you hear this at a party?

Your question:"""
            
            # Call Ollama
            response = requests.post(
                self.api_url,
                json={
                    "model": self.default_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "max_tokens": 50
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                question_text = result.get('response', '').strip()
                
                if question_text and '?' not in question_text:
                    question_text += '?'
                
                if question_text and len(question_text) > 5:
                    return {
                        'feature': 'ai_generated',
                        'value': 'dynamic',
                        'text': question_text,
                        'source': 'ollama',
                        'model': self.default_model
                    }
            
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get Ollama service status"""
        return {
            'available': self.is_available,
            'models': self.available_models,
            'default_model': self.default_model,
            'model_count': len(self.available_models)
        }
