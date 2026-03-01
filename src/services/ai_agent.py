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
        # Normalize API key env vars to avoid dual-key warnings from the SDK.
        # Prefer GEMINI_API_KEY, fallback to GOOGLE_API_KEY.
        gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        google_key = (os.getenv("GOOGLE_API_KEY") or "").strip()

        api_key = gemini_key or google_key
        
        if not api_key:
            raise ValueError(
                "Gemini API key not found in environment variables. "
                "Please set GEMINI_API_KEY (or GOOGLE_API_KEY) in your .env file."
            )

        # Keep a single canonical env var for the process (silences SDK warning).
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ.pop("GOOGLE_API_KEY", None)

        # google-genai client
        self.client = genai.Client(api_key=api_key)

        # Use Gemini 2.5 Flash
        self.model_name = "gemini-2.5-flash"
        
        print("Gemini client initialized successfully")
    
    def extract_cv_text(self, cv_file_path):
        """
        Extract raw text from a PDF CV using Gemini.
        
        Args:
            cv_file_path: Path to the uploaded PDF CV
            
        Returns:
            str: Raw text content of the CV
        """
        try:
            with open(cv_file_path, "rb") as f:
                cv_bytes = f.read()
            
            cv_part = types.Part.from_bytes(data=cv_bytes, mime_type="application/pdf")
            
            prompt = """Extrae TODO el texto de este documento PDF tal cual está escrito. 
No resumas, no interpretes, no cambies nada. Solo devuelve el texto plano completo del documento.
No agregues comentarios ni formato adicional."""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[cv_part, prompt],
            )
            
            return (response.text or "").strip()
        except Exception as e:
            print(f"Error extracting CV text: {e}")
            return ""

    def extract_cv_text(self, cv_file_path):
        """
        Extract raw text from a PDF CV using Gemini.
        
        Args:
            cv_file_path: Path to the uploaded PDF CV
            
        Returns:
            str: Raw text content of the CV
        """
        try:
            with open(cv_file_path, "rb") as f:
                cv_bytes = f.read()
            
            cv_part = types.Part.from_bytes(data=cv_bytes, mime_type="application/pdf")
            
            prompt = """Extrae TODO el texto de este documento PDF tal cual está escrito. 
No resumas, no interpretes, no cambies nada. Solo devuelve el texto plano completo del documento.
No agregues comentarios ni formato adicional."""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[cv_part, prompt],
            )
            
            return (response.text or "").strip()
        except Exception as e:
            print(f"Error extracting CV text: {e}")
            return ""

    def analyze_profile(self, cv_file_path, audio_file_path=None, brain_dump_text=None):
        """
        Analyze CV and optional audio brain dump OR text brain dump using Gemini Flash Lite
        
        Args:
            cv_file_path: Path to the uploaded PDF CV
            audio_file_path: Path to the uploaded audio file (brain dump), optional
            brain_dump_text: Text brain dump written by the user, optional (mutually exclusive with audio)
        
        Returns:
            dict: Analysis results with enriched profile schema
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
            
            # Construct the prompt based on what additional context we have
            base_schema = """Devuelve un objeto JSON con las siguientes claves:
- 'name': nombre completo del estudiante
- 'university': universidad o institución educativa actual
- 'career': carrera o programa de estudios (ej: "Ingeniería en Sistemas", "Medicina", "Administración de Empresas")
- 'study_level': nivel de estudios actual ("pregrado", "licenciatura", "maestría", "doctorado", "recién_egresado")
- 'country': país de residencia o donde estudia
- 'languages': array de idiomas que domina con nivel (ej: ["Español (nativo)", "Inglés (avanzado)"])
- 'top_skills': array de máximo 5 habilidades técnicas principales
- 'interests': array de áreas de interés académico o profesional (ej: ["inteligencia artificial", "finanzas", "investigación médica"])
- 'ambitions': descripción de sus metas y aspiraciones profesionales a mediano/largo plazo
- 'preferred_opportunity_types': array de tipos de oportunidades que busca (ej: ["becas", "pasantías", "investigación", "intercambio", "voluntariado"])
- 'availability': disponibilidad del estudiante ("tiempo_completo", "medio_tiempo", "verano", "flexible")
- 'summary_of_potential': resumen de 2-3 oraciones sobre el potencial único del estudiante

Si algún campo no se puede inferir, usa valores razonables basados en el contexto o "No especificado".
Formatea tu respuesta solo como JSON válido, sin bloques de código markdown."""
            
            # Determine which type of brain dump we have (audio, text, or none)
            if audio_part:
                # Audio brain dump
                prompt = f"""Eres un coach de carrera de clase mundial y experto en análisis de perfiles universitarios. Te proporciono el CV de un estudiante y una nota de voz donde cuenta sobre sí mismo.

Del CV, extrae información detallada sobre el estudiante.
Del audio, extrae su 'potencial oculto', ambiciones, pasiones y contexto personal.

{base_schema}"""
            elif brain_dump_text and brain_dump_text.strip():
                # Text brain dump - append it to content_parts as text
                prompt = f"""Eres un coach de carrera de clase mundial y experto en análisis de perfiles universitarios. Te proporciono el CV de un estudiante y un texto donde el estudiante cuenta sobre sí mismo.

Del CV, extrae información detallada sobre el estudiante.
Del texto personal del estudiante, extrae su 'potencial oculto', ambiciones, pasiones y contexto personal.

TEXTO PERSONAL DEL ESTUDIANTE:
\"\"\"
{brain_dump_text.strip()}
\"\"\"

{base_schema}"""
            else:
                # No additional context, just CV
                prompt = f"""Eres un coach de carrera de clase mundial y experto en análisis de perfiles universitarios. Te proporciono el CV de un estudiante.

Del CV, extrae información detallada sobre el estudiante. Infiere sus ambiciones y potencial basándote únicamente en el contenido del CV.

{base_schema}"""
            
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
            
            # Ensure all required fields are present with enriched schema
            result.setdefault('name', 'Unknown')
            result.setdefault('university', 'No especificado')
            result.setdefault('career', 'No especificado')
            result.setdefault('study_level', 'pregrado')
            result.setdefault('country', 'No especificado')
            result.setdefault('languages', ['Español'])
            result.setdefault('top_skills', [])
            result.setdefault('interests', [])
            result.setdefault('ambitions', 'No ambitions specified')
            result.setdefault('preferred_opportunity_types', ['becas', 'pasantías'])
            result.setdefault('availability', 'flexible')
            result.setdefault('summary_of_potential', 'No summary available')
            
            return result
            
        except Exception as e:
            print(f"Error in analyze_profile: {str(e)}")
            raise


def analyze_profile(cv_file_path, audio_file_path=None, brain_dump_text=None):
    """
    Convenience function to analyze profile using Gemini agent.
    Also extracts raw CV text for use in opportunity searches.
    
    Args:
        cv_file_path: Path to the uploaded PDF CV
        audio_file_path: Path to the uploaded audio file (brain dump), optional
        brain_dump_text: Text brain dump written by the user, optional
    
    Returns:
        tuple: (profile_dict, cv_raw_text)
            - profile_dict: Analysis results with enriched profile schema
            - cv_raw_text: Raw text extracted from CV
    """
    agent = GeminiAgent()
    
    # Extract raw CV text for Perplexity searches
    cv_raw_text = agent.extract_cv_text(cv_file_path)
    
    # Analyze profile for summary display
    profile = agent.analyze_profile(cv_file_path, audio_file_path, brain_dump_text)
    
    return profile, cv_raw_text
