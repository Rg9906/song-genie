"""
Free AI API Integrator
Integrates with free AI services for dynamic question generation
"""

import requests
import json
import random
from typing import List, Dict, Any, Optional
import logging

# Import AI services
try:
    from .gemini_service import GeminiService
except ImportError:
    GeminiService = None

try:
    from .huggingface_service import HuggingFaceService
except ImportError:
    HuggingFaceService = None

try:
    from .groq_service import GroqService
except ImportError:
    GroqService = None

try:
    from .openrouter_service import OpenRouterService
except ImportError:
    OpenRouterService = None

try:
    from .ollama_service_fixed import OllamaService
except ImportError:
    OllamaService = None

logger = logging.getLogger(__name__)

class FreeAIIntegrator:
    """Integrates with multiple free AI services"""
    
    def __init__(self):
        self.services = {}
        
        # Add available services
        if GeminiService:
            self.services['gemini'] = GeminiService()
        if HuggingFaceService:
            self.services['huggingface'] = HuggingFaceService()
        if GroqService:
            self.services['groq'] = GroqService()
        if OpenRouterService:
            self.services['openrouter'] = OpenRouterService()
        if OllamaService:
            self.services['ollama'] = OllamaService()
        
        # Try to initialize services in order of preference
        self.active_service = None
        for service_name, service in self.services.items():
            if service.is_available():
                self.active_service = service
                logger.info(f"🤖 Using {service_name} for AI generation")
                break
        
        if not self.active_service:
            logger.warning("⚠️ No AI services available, using fallback")
    
    def generate_dynamic_questions(self, song_data: List[Dict[str, Any]], 
                                 asked_questions: set, 
                                 context: str = "") -> List[Dict[str, Any]]:
        """Generate dynamic questions using AI"""
        if not self.active_service:
            return self._fallback_generation(song_data, asked_questions)
        
        try:
            return self.active_service.generate_questions(song_data, asked_questions, context)
        except Exception as e:
            logger.warning(f"AI service failed: {e}")
            return self._fallback_generation(song_data, asked_questions)
    
    def _fallback_generation(self, song_data: List[Dict[str, Any]], 
                           asked_questions: set) -> List[Dict[str, Any]]:
        """Fallback question generation without AI"""
        questions = []
        
        # Analyze song data dynamically
        all_attributes = set()
        for song in song_data:
            all_attributes.update(song.keys())
        
        # Remove basic attributes
        all_attributes.discard('id')
        all_attributes.discard('title')
        
        # Generate questions for discovered attributes
        for attr in list(all_attributes)[:10]:  # Limit to 10 attributes
            values = set()
            for song in song_data:
                value = song.get(attr)
                if value:
                    if isinstance(value, list):
                        values.update([str(v) for v in value])
                    else:
                        values.add(str(value))
            
            # Generate questions for unique values
            for value in list(values)[:3]:  # Limit to 3 values per attribute
                key = (attr, value)
                if key not in asked_questions:
                    questions.append({
                        'feature': attr,
                        'value': value,
                        'text': f"Is this connected with {value}?",
                        'source': 'fallback'
                    })
        
        return questions[:5]  # Limit fallback questions

class HuggingFaceService:
    """Hugging Face Inference API integration"""
    
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models"
        self.models = [
            "microsoft/DialoGPT-medium",
            "facebook/blenderbot-400M-distill",
            "microsoft/DialoGPT-large"
        ]
    
    def is_available(self) -> bool:
        """Check if service is available"""
        try:
            # Test with a simple request
            response = requests.get(f"{self.api_url}/microsoft/DialoGPT-medium", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_questions(self, song_data: List[Dict[str, Any]], 
                          asked_questions: set, context: str) -> List[Dict[str, Any]]:
        """Generate questions using Hugging Face"""
        questions = []
        
        # Analyze song attributes
        attributes = self._analyze_attributes(song_data)
        
        for attr, values in attributes.items():
            if len(values) > 1:  # Only if we have variety
                # Generate question about this attribute
                prompt = f"""
                Generate a creative music guessing question about {attr}.
                Available values: {', '.join(list(values)[:5])}
                Make it natural and conversational.
                """
                
                try:
                    response = self._call_api(prompt)
                    if response:
                        questions.append({
                            'feature': attr,
                            'value': 'dynamic',
                            'text': response.strip(),
                            'source': 'huggingface'
                        })
                except Exception as e:
                    logger.warning(f"HuggingFace generation failed: {e}")
        
        return questions[:3]
    
    def _analyze_attributes(self, song_data: List[Dict[str, Any]]) -> Dict[str, set]:
        """Analyze song attributes and their values"""
        attributes = defaultdict(set)
        
        for song in song_data:
            for key, value in song.items():
                if key not in ['id', 'title'] and value:
                    if isinstance(value, list):
                        attributes[key].update([str(v) for v in value])
                    else:
                        attributes[key].add(str(value))
        
        return dict(attributes)
    
    def _call_api(self, prompt: str) -> Optional[str]:
        """Call Hugging Face API"""
        model = random.choice(self.models)
        
        try:
            response = requests.post(
                f"{self.api_url}/{model}",
                headers={"Authorization": f"Bearer hf_your_token_here"},  # User needs to add token
                json={"inputs": prompt}
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    return result[0].get('generated_text', '')
            
            return None
        except Exception as e:
            logger.warning(f"HuggingFace API call failed: {e}")
            return None

class GroqService:
    """Groq API integration (fast, free tier)"""
    
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.models = [
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
    
    def is_available(self) -> bool:
        """Check if service is available"""
        # User needs to provide API key
        return False  # Disable until user provides key
    
    def generate_questions(self, song_data: List[Dict[str, Any]], 
                          asked_questions: set, context: str) -> List[Dict[str, Any]]:
        """Generate questions using Groq"""
        # Implementation would go here
        return []

class OpenRouterService:
    """OpenRouter API integration (many free models)"""
    
    def __init__(self):
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.models = [
            "meta-llama/llama-3-8b-instruct",
            "microsoft/wizardlm-2-8x22b",
            "anthropic/claude-3-haiku"
        ]
    
    def is_available(self) -> bool:
        """Check if service is available"""
        return False  # Disable until user provides key
    
    def generate_questions(self, song_data: List[Dict[str, Any]], 
                          asked_questions: set, context: str) -> List[Dict[str, Any]]:
        """Generate questions using OpenRouter"""
        return []

class OllamaService:
    """Ollama local service integration"""
    
    def __init__(self):
        self.api_url = "http://localhost:11434/api/generate"
        self.models = ["phi3", "llama3:8b", "mistral"]
    
    def is_available(self) -> bool:
        """Check if Ollama is running locally"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def generate_questions(self, song_data: List[Dict[str, Any]], 
                          asked_questions: set, context: str) -> List[Dict[str, Any]]:
        """Generate questions using Ollama"""
        questions = []
        
        # Get available models
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                if models:
                    model = random.choice(models)
                    
                    # Analyze song data
                    attributes = self._get_sample_attributes(song_data)
                    
                    for attr, sample_values in attributes.items():
                        prompt = f"""Generate a creative music guessing question about {attr}.
                        Here are some example values: {', '.join(sample_values[:3])}
                        Make it sound natural and engaging.
                        Keep it under 20 words.
                        Question:"""
                        
                        try:
                            ollama_response = requests.post(
                                self.api_url,
                                json={
                                    "model": model,
                                    "prompt": prompt,
                                    "stream": False
                                }
                            )
                            
                            if ollama_response.status_code == 200:
                                result = ollama_response.json()
                                question_text = result.get('response', '').strip()
                                
                                if question_text:
                                    questions.append({
                                        'feature': attr,
                                        'value': 'dynamic',
                                        'text': question_text,
                                        'source': 'ollama'
                                    })
                        except Exception as e:
                            logger.warning(f"Ollama generation failed: {e}")
        
        except Exception as e:
            logger.warning(f"Ollama service unavailable: {e}")
        
        return questions[:3]  # Limit Ollama questions
    
    def _get_sample_attributes(self, song_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Get sample attributes from song data"""
        attributes = defaultdict(list)
        
        for song in song_data[:10]:  # Sample first 10 songs
            for key, value in song.items():
                if key not in ['id', 'title'] and value:
                    if isinstance(value, list):
                        attributes[key].extend([str(v) for v in value[:2]])
                    else:
                        attributes[key].append(str(value))
        
        # Remove duplicates and limit
        return {k: list(set(v))[:5] for k, v in attributes.items() if v}
