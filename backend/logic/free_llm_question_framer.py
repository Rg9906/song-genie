"""
Free LLM Question Framer
Uses free language models for dynamic question generation
"""

import random
import json
import requests
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FreeLLMQuestionFramer:
    """Uses free language models to reframe questions dynamically"""
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        self.framing_styles = self._load_framing_styles()
        
    def _load_framing_styles(self) -> Dict[str, List[str]]:
        """Load different question framing styles"""
        return {
            'casual': [
                "So, is this {value}?",
                "Would you say this is {value}?",
                "I'm guessing this is {value}, right?",
                "This feels like {value}, yeah?",
                "You'd call this {value}, wouldn't you?"
            ],
            'formal': [
                "Would you classify this as {value}?",
                "Is this accurately described as {value}?",
                "Does this fall under the category of {value}?",
                "Would the term {value} be appropriate here?"
            ],
            'enthusiastic': [
                "OMG, is this totally {value}?",
                "Wait, is this like, super {value}?",
                "This has to be {value}, right?!",
                "I'm getting major {value} vibes here!"
            ],
            'mysterious': [
                "Could this be shrouded in {value}?",
                "Does this whisper tales of {value}?",
                "Might this be cloaked in {value}?",
                "Is there an essence of {value} here?"
            ],
            'technical': [
                "Would you analyze this as {value}?",
                "Does this exhibit characteristics of {value}?",
                "Would this be categorized as {value} technically?",
                "Does this align with {value} parameters?"
            ],
            'poetic': [
                "Does this paint with colors of {value}?",
                "Is this a symphony of {value}?",
                "Does this dance in the realm of {value}?",
                "Would you find poetry in {value} here?"
            ],
            'direct': [
                "Is this {value}?",
                "Is it {value}?",
                "Would you say {value}?",
                "Simply put: {value}?"
            ],
            'conversational': [
                "Let me ask you... is this {value}?",
                "I'm curious - would you say this is {value}?",
                "Tell me, does this feel like {value}?",
                "What's your take - is this {value}?"
            ]
        }
    
    def frame_question(self, base_question: Dict[str, Any], style: Optional[str] = None) -> Dict[str, Any]:
        """Reframe a question with different style"""
        if style is None:
            style = random.choice(list(self.framing_styles.keys()))
        
        feature = base_question['feature']
        value = base_question['value']
        
        # Get appropriate templates for this feature
        templates = self.framing_styles.get(style, self.framing_styles['casual'])
        
        # Select random template
        template = random.choice(templates)
        
        # Frame the question
        framed_text = template.format(value=value)
        
        # Add some variety based on feature type
        if feature == 'genres':
            framed_text = self._add_genre_flair(framed_text, style)
        elif feature == 'artists':
            framed_text = self._add_artist_flair(framed_text, style)
        elif feature == 'themes':
            framed_text = self._add_theme_flair(framed_text, style)
        
        return {
            'feature': feature,
            'value': value,
            'text': framed_text,
            'style': style,
            'original_text': base_question['text']
        }
    
    def _add_genre_flair(self, text: str, style: str) -> str:
        """Add genre-specific flair"""
        genre_flairs = {
            'casual': [" vibe", " energy", " feel"],
            'formal': [" characteristics", " elements", " qualities"],
            'enthusiastic': [" ENERGY!", " VIBES!", " FEEL!"],
            'mysterious': [" essence", " aura", " mystery"],
            'technical': [" signature", " profile", " markers"],
            'poetic': [" melody", " harmony", " rhythm"]
        }
        
        flairs = genre_flairs.get(style, [""])
        flair = random.choice(flairs)
        
        if flair and random.random() > 0.5:
            return text.replace("?", f" with{flair}?")
        
        return text
    
    def _add_artist_flair(self, text: str, style: str) -> str:
        """Add artist-specific flair"""
        artist_flairs = {
            'casual': [" track", " song", " tune"],
            'formal': [" composition", " piece", " work"],
            'enthusiastic': [" BANGER!", " JAM!", " HIT!"],
            'mysterious': [" creation", " masterpiece", " work"],
            'technical': [" production", " recording", " piece"],
            'poetic': [" creation", " art", " masterpiece"]
        }
        
        flairs = artist_flairs.get(style, [""])
        flair = random.choice(flairs)
        
        if flair and random.random() > 0.5:
            return text.replace("this", f"this {flair}")
        
        return text
    
    def _add_theme_flair(self, text: str, style: str) -> str:
        """Add theme-specific flair"""
        theme_flairs = {
            'casual': [" about", " dealing with", " focused on"],
            'formal': [" concerning", " regarding", " pertaining to"],
            'enthusiastic': [" ALL ABOUT", " TOTALLY", " 100%"],
            'mysterious': [" hinting at", " suggesting", " evoking"],
            'technical': [" addressing", " exploring", " examining"],
            'poetic': [" whispering of", " singing of", " dancing with"]
        }
        
        flairs = theme_flairs.get(style, [""])
        flair = random.choice(flairs)
        
        if flair and random.random() > 0.5:
            # Add flair after the value
            parts = text.split(value)
            if len(parts) == 2:
                return f"{parts[0]}{value}{flair}{parts[1]}"
        
        return text
    
    def frame_multiple_questions(self, questions: List[Dict[str, Any]], 
                                ensure_style_variety: bool = True) -> List[Dict[str, Any]]:
        """Frame multiple questions with style variety"""
        framed_questions = []
        used_styles = set()
        
        for question in questions:
            if ensure_style_variety:
                # Try to use different styles
                available_styles = [s for s in self.framing_styles.keys() 
                                 if s not in used_styles]
                
                if not available_styles:
                    used_styles.clear()
                    available_styles = list(self.framing_styles.keys())
                
                style = random.choice(available_styles)
                used_styles.add(style)
            else:
                style = None
            
            framed = self.frame_question(question, style)
            framed_questions.append(framed)
        
        return framed_questions
    
    def call_free_llm(self, prompt: str) -> Optional[str]:
        """Call a free LLM API for question generation (placeholder)"""
        # This is a placeholder for when you want to integrate actual LLMs
        # You could use:
        # - Ollama (local models)
        # - Hugging Face Inference API (free tier)
        # - Groq (free tier)
        # - OpenRouter (free models)
        
        if not self.use_llm:
            return None
        
        try:
            # Example: Ollama API call
            # response = requests.post("http://localhost:11434/api/generate", 
            #                         json={
            #                             "model": "llama2",
            #                             "prompt": prompt,
            #                             "stream": False
            #                         })
            # if response.status_code == 200:
            #     return response.json().get("response", "")
            
            # For now, return None to use template-based framing
            return None
            
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
            return None
    
    def generate_llm_framed_question(self, base_question: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a question using actual LLM"""
        prompt = f"""
        Rephrase this music question in a natural, conversational way:
        
        Original: "{base_question['text']}"
        Feature: {base_question['feature']}
        Value: {base_question['value']}
        
        Make it sound like a friendly music guessing game. Keep it concise.
        """
        
        llm_response = self.call_free_llm(prompt)
        
        if llm_response:
            return {
                'feature': base_question['feature'],
                'value': base_question['value'],
                'text': llm_response.strip(),
                'style': 'llm_generated',
                'original_text': base_question['text']
            }
        else:
            # Fallback to template-based framing
            return self.frame_question(base_question)
