"""
Gemini API Service for AI Question Generation
Uses Google's Gemini API for creative question generation
"""

import requests
import json
import random
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class GeminiService:
    """Gemini API service for AI question generation"""
    
    def __init__(self, api_key: str = None):
        # Use provided API key, environment variable, or the hardcoded key
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or "AIzaSyAf_1B4Ipta6N753Qu-w4HeEegKLRMUqOE"
        self.api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"
        
        # Check if API key is available
        self.is_available = bool(self.api_key)
        
        if self.is_available:
            logger.info("🤖 Gemini API service initialized")
        else:
            logger.warning("⚠️ Gemini API key not found")
    
    def generate_question(self, song_data: List[Dict[str, Any]], 
                         asked_questions: set) -> Optional[Dict[str, Any]]:
        """Generate a question using Gemini API"""
        if not self.is_available:
            return None
        
        try:
            # Get sample songs for context
            sample_songs = random.sample(song_data, min(3, len(song_data)))
            
            # Extract some attributes for the prompt
            sample_artists = []
            sample_genres = []
            sample_themes = []
            
            for song in sample_songs:
                if 'artists' in song and song['artists']:
                    sample_artists.extend(song['artists'][:2])
                if 'genres' in song and song['genres']:
                    sample_genres.extend(song['genres'][:2])
                if 'themes' in song and song['themes']:
                    sample_themes.extend(song['themes'][:2])
            
            # Create creative prompt
            prompt = f"""Generate a short music guessing question.

Artists: {', '.join(set(sample_artists[:3]))}
Genres: {', '.join(set(sample_genres[:3]))}

Generate ONE question under 15 words. Examples:
- "Would this get you dancing?"
- "Does this sound like summer?"
- "Is this more of a chill vibe?"

Question:"""
            
            # Call Gemini API
            headers = {
                "Content-Type": "application/json",
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.8,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 200,
                    "candidateCount": 1
                }
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            logger.info(f"Gemini API response status: {response.status_code}")
            logger.info(f"Gemini API response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract the generated text
                if 'candidates' in result and result['candidates']:
                    generated_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # Clean up the response
                    if generated_text:
                        # Remove quotes if present
                        if generated_text.startswith('"') and generated_text.endswith('"'):
                            generated_text = generated_text[1:-1]
                        
                        # Ensure it ends with a question mark
                        if not generated_text.endswith('?'):
                            generated_text += '?'
                        
                        # Validate it's a good question
                        if len(generated_text) > 5 and len(generated_text) < 100:
                            return {
                                'feature': 'ai_generated',
                                'value': 'dynamic',
                                'text': generated_text,
                                'source': 'gemini',
                                'model': 'gemini-2.0-flash'
                            }
            
        except Exception as e:
            logger.warning(f"Gemini API generation failed: {e}")
        
        return None
    
    def generate_multiple_questions(self, song_data: List[Dict[str, Any]], 
                                  asked_questions: set, 
                                  num_questions: int = 3) -> List[Dict[str, Any]]:
        """Generate multiple questions using Gemini API"""
        questions = []
        
        for i in range(num_questions):
            question = self.generate_question(song_data, asked_questions)
            if question:
                questions.append(question)
                # Add to asked questions to avoid duplicates
                asked_questions.add((question['feature'], question['value']))
        
        return questions
    
    def improve_question_text(self, original_question: str) -> Optional[str]:
        """Improve an existing question text using Gemini"""
        if not self.is_available:
            return None
        
        try:
            prompt = f"""Improve this music guessing question to make it more natural and conversational:

Original: "{original_question}"

Make it sound like a friendly music expert talking to a friend.
Keep it short and engaging.
Don't be too technical.
Make it under 20 words.

Improved question:"""
            
            headers = {
                "Content-Type": "application/json",
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 40
                }
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'candidates' in result and result['candidates']:
                    improved_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # Clean up
                    if improved_text.startswith('"') and improved_text.endswith('"'):
                        improved_text = improved_text[1:-1]
                    
                    if not improved_text.endswith('?'):
                        improved_text += '?'
                    
                    return improved_text if len(improved_text) > 5 else None
            
        except Exception as e:
            logger.warning(f"Gemini improvement failed: {e}")
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get Gemini service status"""
        return {
            'available': self.is_available,
            'api_key_set': bool(self.api_key),
            'model': 'gemini-2.0-flash',
            'provider': 'Google'
        }
