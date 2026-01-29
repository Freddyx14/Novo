"""
AI Agent service for Gemini API interactions
Handles multimodal analysis of CV and audio files
"""

import os
import json
import re
from dotenv import load_dotenv

from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

class GeminiAgent:
    """Wrapper class for Google Gemini API interactions"""
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        # Support both env var names (some docs use GOOGLE_API_KEY)
        api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        
        if not api_key:
            raise ValueError(
                "Gemini API key not found in environment variables. "
                "Please set GEMINI_API_KEY (or GOOGLE_API_KEY) in your .env file."
            )

        # google-genai client
        self.client = genai.Client(api_key=api_key)

        # Use the requested fast model
        self.model_name = "gemini-flash-lite-latest"
        
        print("Gemini client initialized successfully")
    
    def analyze_profile(self, cv_file_path, audio_file_path=None):
        """
        Analyze CV and optional audio brain dump using Gemini Flash Lite
        
        Args:
            cv_file_path: Path to the uploaded PDF CV
            audio_file_path: Path to the uploaded audio file (brain dump), optional
        
        Returns:
            dict: Analysis results with name, top_skills, ambitions, summary_of_potential
        """
        try:
            # Read CV PDF file
            with open(cv_file_path, "rb") as f:
                cv_bytes = f.read()

            cv_part = types.Part.from_bytes(data=cv_bytes, mime_type="application/pdf")
            
            print(f"CV file loaded: {cv_file_path}")
            
            # Prepare content parts
            content_parts = [cv_part]
            
            # Read audio file if provided
            audio_part = None
            if audio_file_path and os.path.exists(audio_file_path):
                # Determine MIME type based on file extension
                audio_ext = os.path.splitext(audio_file_path)[1].lower()
                mime_types = {
                    '.mp3': 'audio/mpeg',
                    '.wav': 'audio/wav',
                    '.m4a': 'audio/mp4',
                    '.ogg': 'audio/ogg'
                }
                mime_type = mime_types.get(audio_ext, 'audio/mpeg')
                
                with open(audio_file_path, "rb") as f:
                    audio_bytes = f.read()

                audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
                
                print(f"Audio file loaded: {audio_file_path}")
                content_parts.append(audio_part)
            
            # Construct the prompt
            prompt = """Eres un coach de carrera de clase mundial. Te proporciono el CV de un estudiante y una nota de voz 'brain dump'.

Del CV, extrae sus habilidades técnicas (hard skills) y experiencia.

Del audio, extrae su 'potencial oculto', ambiciones y contexto cultural.

Devuelve un objeto JSON con las claves: 'name', 'top_skills', 'ambitions', y 'summary_of_potential'.
Los valores de texto deben estar explicados en ESPAÑOL.

Formatea tu respuesta solo como JSON válido, sin bloques de código markdown."""
            
            # If no audio file, update the prompt
            if not audio_part:
                prompt = """Eres un coach de carrera de clase mundial. Te proporciono el CV de un estudiante.

Del CV, extrae sus habilidades técnicas (hard skills) y experiencia.

Devuelve un objeto JSON con las claves: 'name', 'top_skills', 'ambitions', y 'summary_of_potential'.
Los valores de texto deben estar explicados en ESPAÑOL.

Como no hay audio, basa las ambiciones y el summary_of_potential solo en el contenido del CV.

Formatea tu respuesta solo como JSON válido, sin bloques de código markdown."""
            
            # Generate content
            print("Sending request to Gemini...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=content_parts + [prompt],
            )
            
            # Extract JSON from response
            response_text = (response.text or "").strip()
            
            # Clean up JSON if wrapped in markdown code blocks
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from the text
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback: return structured response
                    result = {
                        'name': 'Unknown',
                        'top_skills': [],
                        'ambitions': 'Could not parse response',
                        'summary_of_potential': response_text
                    }
            
            # Ensure all required fields are present
            result.setdefault('name', 'Unknown')
            result.setdefault('top_skills', [])
            result.setdefault('ambitions', 'No ambitions specified')
            result.setdefault('summary_of_potential', 'No summary available')
            
            return result
            
        except Exception as e:
            print(f"Error in analyze_profile: {str(e)}")
            raise


def analyze_profile(cv_file_path, audio_file_path=None):
    """
    Convenience function to analyze profile using Gemini agent
    
    Args:
        cv_file_path: Path to the uploaded PDF CV
        audio_file_path: Path to the uploaded audio file (brain dump), optional
    
    Returns:
        dict: Analysis results with name, top_skills, ambitions, summary_of_potential
    """
    agent = GeminiAgent()
    return agent.analyze_profile(cv_file_path, audio_file_path)
