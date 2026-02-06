import os
import json
import requests
import google.generativeai as genai
from supabase import create_client, Client

# Setup: Initialize Gemini and Supabase clients
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-flash-lite-latest")

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)


# Inside src/services/hunter.py

def search_opportunities_with_perplexity(profile_data, num_results=3):
    """
    Uses Perplexity to find real opportunities (internships, fellowships, programs, research positions, etc.) based on profile.
    """
    print("🔎 Asking Perplexity to search for opportunities...")
    
    # Extract enriched profile data
    name = profile_data.get('name', 'Estudiante')
    university = profile_data.get('university', '')
    career = profile_data.get('career', '')
    study_level = profile_data.get('study_level', 'pregrado')
    country = profile_data.get('country', 'Latinoamérica')
    languages = profile_data.get('languages', ['Español'])
    skills = profile_data.get('top_skills', [])
    interests = profile_data.get('interests', [])
    ambitions = profile_data.get('ambitions', '')
    preferred_types = profile_data.get('preferred_opportunity_types', ['becas', 'pasantías'])
    availability = profile_data.get('availability', 'flexible')
    
    # Build comprehensive student context
    student_context = f"Estudiante de {career if career else 'universidad'}" if career else "Estudiante universitario"
    if study_level:
        student_context += f" ({study_level})"
    if country and country != 'No especificado':
        student_context += f" en {country}"
    
    # Build interests and skills string
    interest_text = ", ".join(interests[:4]) if interests else ""
    skills_text = ", ".join(skills[:3]) if skills else ""
    preferred_types_text = ", ".join(preferred_types[:3]) if preferred_types else "becas, pasantías"
    languages_text = ", ".join(languages[:2]) if languages else "Español"
    
    # Build rich search query
    search_parts = []
    if ambitions:
        search_parts.append(f"Ambiciones: {ambitions}")
    if interest_text:
        search_parts.append(f"Intereses: {interest_text}")
    if skills_text:
        search_parts.append(f"Habilidades: {skills_text}")
    
    search_query = f"{student_context}. {' '.join(search_parts)}. Busca: {preferred_types_text}. Idiomas: {languages_text}."
    
    url = "https://api.perplexity.ai/chat/completions"
    
    # Build detailed system prompt with student context
    system_prompt = f"""Eres un buscador experto de oportunidades educativas y profesionales para estudiantes universitarios.

PERFIL DEL ESTUDIANTE:
- Contexto: {student_context}
- Carrera: {career if career else 'No especificada'}
- Nivel: {study_level}
- País: {country}
- Idiomas: {languages_text}
- Habilidades: {skills_text if skills_text else 'No especificadas'}
- Intereses: {interest_text if interest_text else 'No especificados'}
- Ambiciones: {ambitions if ambitions else 'No especificadas'}
- Tipos de oportunidades preferidas: {preferred_types_text}
- Disponibilidad: {availability}

TU TAREA:
1. Busca {num_results} oportunidades REALES, ACTUALES y VERIFICABLES que existan en 2025-2026
2. Prioriza oportunidades que:
   - Sean ELEGIBLES para el nivel de estudios del estudiante ({study_level})
   - Estén disponibles para estudiantes de {country} o sean internacionales
   - Coincidan con sus intereses y carrera
   - Se alineen con sus ambiciones profesionales
3. Incluye variedad: becas, pasantías, programas de investigación, intercambios, concursos, etc.
4. SOLO incluye oportunidades con requisitos que el estudiante PODRÍA cumplir

FORMATO DE RESPUESTA:
Devuelve SOLO un array JSON válido, sin texto adicional:
[
  {{
    "title": "Nombre exacto del programa/beca",
    "company": "Organización que lo ofrece",
    "location": "País/Ciudad o Remoto",
    "url": "URL oficial verificable",
    "description": "Descripción breve en español",
    "opportunity_type": "beca|pasantía|investigación|intercambio|concurso|voluntariado",
    "eligibility_level": "pregrado|maestría|doctorado|todos",
    "deadline_info": "Información sobre fechas límite si está disponible"
  }}
]"""
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Encuentra {num_results} oportunidades específicas y actuales para este estudiante. Prioriza calidad sobre cantidad y asegúrate de que sean elegibles para su perfil."
            }
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # DEBUG: Print what Perplexity actually sent back
        raw_content = response.json()['choices'][0]['message']['content']
        print(f"📝 Raw Perplexity Response: {raw_content[:200]}...") # Print first 200 chars
        
        # Clean up code blocks if Perplexity adds them (```json ... ```)
        clean_content = raw_content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(clean_content)
        
    except Exception as e:
        print(f"❌ Error parsing Perplexity response: {e}")
        print(f"Raw content was: {response.text if 'response' in locals() else 'No response'}")
        return []


def evaluate_match(student_profile, opportunity):
    """
    Uses Gemini to evaluate how well a student profile matches an opportunity.
    Returns a dict with 'score' (0-100), 'reason' (string), and 'is_eligible' (boolean).
    Uses weighted criteria for more accurate scoring.
    """
    # Extract student context for better evaluation
    study_level = student_profile.get('study_level', 'pregrado')
    country = student_profile.get('country', 'No especificado')
    career = student_profile.get('career', 'No especificada')
    
    prompt = f"""Eres un asesor académico experto. Evalúa si este estudiante es un BUEN CANDIDATO para esta oportunidad.

PERFIL DEL ESTUDIANTE:
{json.dumps(student_profile, ensure_ascii=False, indent=2)}

OPORTUNIDAD:
{json.dumps(opportunity, ensure_ascii=False, indent=2)}

EVALÚA CON ESTOS CRITERIOS PONDERADOS:
1. ELEGIBILIDAD (40%): ¿El estudiante cumple los requisitos básicos?
   - ¿Su nivel de estudios ({study_level}) es compatible con la oportunidad?
   - ¿Su país ({country}) es elegible o la oportunidad es internacional?
   - ¿Su carrera ({career}) es relevante para la oportunidad?
   
2. ALINEACIÓN DE INTERESES (30%): ¿Los intereses y ambiciones del estudiante coinciden con el enfoque de la oportunidad?

3. HABILIDADES (20%): ¿Las habilidades del estudiante son relevantes para la oportunidad?

4. POTENCIAL DE IMPACTO (10%): ¿Esta oportunidad ayudaría significativamente al desarrollo profesional del estudiante?

IMPORTANTE:
- Si el estudiante NO ES ELEGIBLE por nivel de estudios o país, el score debe ser menor a 50
- Solo da scores altos (70+) si hay una alineación clara y el estudiante es elegible

Devuelve un JSON con:
- 'is_eligible': (boolean) ¿El estudiante cumple los requisitos básicos para aplicar?
- 'score': (integer 0-100) Puntuación ponderada según los criterios anteriores
- 'description': (string) Descripción breve de 1-2 frases sobre el programa
- 'reason': (string) Explicación de por qué es o no es un buen match
- 'eligibility_notes': (string) Notas sobre requisitos que podría o no cumplir
"""
    
    try:
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Try to extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse the JSON response
        result = json.loads(response_text)
        
        # Validate the response has required fields
        if 'score' not in result:
            return {"score": 0, "reason": "Invalid response format from AI", "description": "", "is_eligible": False}
        
        # Ensure score is an integer between 0 and 100
        score = int(result['score'])
        score = max(0, min(100, score))
        
        # Get eligibility status (default to True for backwards compatibility)
        is_eligible = result.get('is_eligible', True)
        
        return {
            "score": score,
            "is_eligible": is_eligible,
            "description": result.get('description', ''),
            "reason": result.get('reason', ''),
            "eligibility_notes": result.get('eligibility_notes', '')
        }
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
        return {"score": 0, "reason": "Failed to parse AI response", "description": "", "is_eligible": False}
    
    except Exception as e:
        print(f"Error evaluating match: {e}")
        return {"score": 0, "reason": "Error during evaluation", "description": "", "is_eligible": False}


def find_and_save_matches(student_id, num_results=3):
    """
    Main logic: Fetches student, gets opportunities, scores them, and saves matches.
    """
    try:
        # 1. Fetch the student row
        response = supabase.table("students").select("*").eq("id", student_id).execute()
        
        if not response.data or len(response.data) == 0:
            print(f"No student found with ID: {student_id}")
            return {"error": "Student not found"}
        
        student_row = response.data[0]
        
        # 2. Extract the Profile Data (Safe Parsing)
        # The skills are inside the 'profile_data' column, not the top-level row
        profile_data = student_row.get('profile_data', {})
        
        # If Supabase returned it as a string, parse it into a Dict
        if isinstance(profile_data, str):
            try:
                profile_data = json.loads(profile_data)
                print("Parsed profile_data from string.")
            except:
                profile_data = {}

        print(f"Processing matches for student: {student_row.get('name', 'Unknown')}")

        # 3. Search using the Dictionary (Fixes the error!)
        # We pass the full profile_data dict so the function can find 'top_skills'
        opportunities = search_opportunities_with_perplexity(profile_data, num_results=num_results)
        
        print(f"Found {len(opportunities)} opportunities to evaluate")
        
        matches_saved = 0
        
        # 4. Evaluate and Save
        for opportunity in opportunities:
            # Validate opportunity is a dictionary
            if not isinstance(opportunity, dict):
                print(f"Skipping invalid opportunity: {opportunity}")
                continue
            
            title = opportunity.get('title', 'Unknown Position')
            print(f"\nEvaluating: {title}")
            
            # Score with Gemini (now includes eligibility check)
            evaluation = evaluate_match(profile_data, opportunity)
            score = evaluation['score']
            reason = evaluation['reason']
            description = evaluation.get('description', '')
            is_eligible = evaluation.get('is_eligible', True)
            eligibility_notes = evaluation.get('eligibility_notes', '')
            
            # Get additional opportunity metadata if available
            opportunity_type = opportunity.get('opportunity_type', 'oportunidad')
            deadline_info = opportunity.get('deadline_info', '')
            
            print(f"Score: {score}/100 | Eligible: {is_eligible} - {reason}")
            
            # New threshold: Must be eligible AND score >= 50 (more inclusive but accurate)
            if is_eligible and score >= 50:
                try:
                    # Build rich match reason with all available info
                    full_reason_parts = []
                    if description:
                        full_reason_parts.append(description)
                    if deadline_info:
                        full_reason_parts.append(f"📅 {deadline_info}")
                    full_reason_parts.append(f"💡 Match: {reason}")
                    if eligibility_notes:
                        full_reason_parts.append(f"✅ Elegibilidad: {eligibility_notes}")
                    
                    full_reason = "\n\n".join(full_reason_parts)

                    match_data = {
                        "student_id": student_id,
                        "title": opportunity.get('title', 'Untitled'),
                        "company": opportunity.get('company', 'Unknown'),
                        "location": opportunity.get('location', 'Unknown'),
                        "match_score": score,
                        "match_reason": full_reason,
                        "source_url": opportunity.get('url', None)
                    }
                    
                    supabase.table("matches").insert(match_data).execute()
                    matches_saved += 1
                    print(f"✓ Saved match to database")
                
                except Exception as e:
                    print(f"Error saving match: {e}")
            else:
                skip_reason = "Not eligible" if not is_eligible else f"Score too low ({score}/100)"
                print(f"⊘ Skipped: {skip_reason}")
        
        print(f"\n{'='*50}")
        print(f"Summary: {matches_saved} matches saved out of {len(opportunities)} opportunities")
        
        return {
            "student_id": student_id,
            "opportunities_evaluated": len(opportunities),
            "matches_saved": matches_saved
        }
    
    except Exception as e:
        print(f"Error in find_and_save_matches: {e}")
        return {"error": str(e)}
