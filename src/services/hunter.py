import os
import json
import requests
import google.generativeai as genai
from supabase import create_client, Client

# Setup: Initialize Gemini and Supabase clients
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

########################################
#########   SOLO ES TEMPORAL   #########
########################################
# Toggle entre Perplexity (real) y Gemini (temporal para testing)
USE_GEMINI_FOR_SEARCH = True  # Cambiar a False cuando Perplexity funcione


def search_opportunities_with_gemini(cv_raw_text, brain_dump_text="", profile_data=None, num_results=3):
    """
    TEMPORAL: Usa Gemini para generar oportunidades basadas en el perfil del estudiante.
    NOTA: Estas NO son oportunidades verificadas en tiempo real, son sintéticas para testing.
    """
    print("🤖 Usando Gemini para generar oportunidades (MODO TEMPORAL)...")
    
    # Build student context
    if not cv_raw_text and profile_data:
        cv_raw_text = f"""Nombre: {profile_data.get('name', 'Estudiante')}
Universidad: {profile_data.get('university', 'No especificada')}
Carrera: {profile_data.get('career', 'No especificada')}
Nivel: {profile_data.get('study_level', 'pregrado')}
País: {profile_data.get('country', 'No especificado')}
Idiomas: {', '.join(profile_data.get('languages', ['Español']))}
Habilidades: {', '.join(profile_data.get('top_skills', []))}
Intereses: {', '.join(profile_data.get('interests', []))}
Ambiciones: {profile_data.get('ambitions', 'No especificadas')}"""
    
    student_context = f"CV:\n{cv_raw_text[:4000]}"
    if brain_dump_text and brain_dump_text.strip():
        student_context += f"\n\nContexto adicional:\n{brain_dump_text[:1000]}"
    
    prompt = f"""Basándote en este perfil de estudiante, genera {num_results} oportunidades educativas/profesionales REALISTAS Y RELEVANTES.

{student_context}

IMPORTANTE:
- Genera oportunidades que sean ADECUADAS para el nivel de estudios, país y perfil del estudiante
- Incluye variedad: becas, pasantías, programas de investigación, intercambios, concursos, etc.
- Usa nombres de programas que suenen realistas (pueden ser inspirados en programas reales)
- Incluye URLs realistas (pueden ser ficticias pero deben parecer reales)

Devuelve SOLO un array JSON válido, sin texto adicional:
[
  {{
    "title": "Nombre del programa",
    "company": "Organización",
    "location": "País/Ciudad o Remoto",
    "url": "https://ejemplo.com/programa",
    "description": "Descripción breve",
    "opportunity_type": "beca|pasantía|investigación|intercambio|concurso",
    "eligibility_level": "pregrado|maestría|doctorado|todos",
    "deadline_info": "Plazo de aplicación"
  }}
]"""
    
    try:
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        opportunities = json.loads(response_text)
        print(f"✓ Gemini generó {len(opportunities)} oportunidades")
        return opportunities
        
    except Exception as e:
        print(f"❌ Error con Gemini: {e}")
        return []
########################################
#########   SOLO ES TEMPORAL   #########
########################################

def search_opportunities_with_perplexity(cv_raw_text, brain_dump_text="", profile_data=None, num_results=3):
    """
    Uses Perplexity to find real opportunities based on the FULL raw CV text
    and optional brain dump context. This approach sends complete student info
    instead of extracted variables for more accurate results.
    
    Args:
        cv_raw_text: Full text extracted from the student's CV
        brain_dump_text: Additional context written by the student
        profile_data: Structured profile data (used only for basic metadata fallback)
        num_results: Number of opportunities to find
    """
    print("🔎 Asking Perplexity to search for opportunities (full-text mode)...")
    
    # Use profile_data only for basic metadata if raw text is missing
    if not cv_raw_text and profile_data:
        # Fallback: build context from profile_data like before
        cv_raw_text = f"""Nombre: {profile_data.get('name', 'Estudiante')}
Universidad: {profile_data.get('university', 'No especificada')}
Carrera: {profile_data.get('career', 'No especificada')}
Nivel: {profile_data.get('study_level', 'pregrado')}
País: {profile_data.get('country', 'No especificado')}
Idiomas: {', '.join(profile_data.get('languages', ['Español']))}
Habilidades: {', '.join(profile_data.get('top_skills', []))}
Intereses: {', '.join(profile_data.get('interests', []))}
Ambiciones: {profile_data.get('ambitions', 'No especificadas')}"""
    
    # Build the full student context from raw texts
    student_full_context = f"=== CV COMPLETO DEL ESTUDIANTE ===\n{cv_raw_text}"
    
    if brain_dump_text and brain_dump_text.strip():
        student_full_context += f"\n\n=== CONTEXTO ADICIONAL DEL ESTUDIANTE (escrito por él/ella) ===\n{brain_dump_text.strip()}"
    
    # Truncate if too long for API (keep under ~12000 chars for the student context)
    if len(student_full_context) > 12000:
        student_full_context = student_full_context[:12000] + "\n[...texto truncado por longitud]"
    
    url = "https://api.perplexity.ai/chat/completions"
    
    system_prompt = f"""Eres un buscador experto de oportunidades educativas y profesionales para estudiantes universitarios.

A continuación tienes el CV COMPLETO de un estudiante y contexto adicional que él/ella proporcionó. Usa TODA esta información para encontrar las oportunidades más relevantes.

{student_full_context}

TU TAREA:
1. Analiza profundamente el perfil completo del estudiante (su experiencia, educación, habilidades, idiomas, país, nivel de estudios, intereses y ambiciones)
2. Busca {num_results} oportunidades REALES, ACTUALES y VERIFICABLES que existan en 2025-2026
3. Prioriza oportunidades que:
   - Sean ELEGIBLES para el nivel de estudios y país del estudiante
   - Se alineen con su experiencia, carrera e intereses
   - Coincidan con sus ambiciones y metas profesionales
   - Aprovechen sus idiomas y habilidades únicas
4. Incluye variedad: becas, pasantías, programas de investigación, intercambios, concursos, fellowships, etc.
5. SOLO incluye oportunidades con requisitos que el estudiante PODRÍA cumplir basándote en su CV completo

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
                "content": f"Basándote en el CV completo y el contexto del estudiante, encuentra {num_results} oportunidades específicas, actuales y verificables. Prioriza calidad y relevancia real para este perfil específico."
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
        
        raw_content = response.json()['choices'][0]['message']['content']
        print(f"📝 Raw Perplexity Response: {raw_content[:200]}...")
        
        clean_content = raw_content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(clean_content)
        
    except Exception as e:
        print(f"❌ Error parsing Perplexity response: {e}")
        print(f"Raw content was: {response.text if 'response' in locals() else 'No response'}")
        return []


def evaluate_match(cv_raw_text, brain_dump_text, opportunity, profile_data=None):
    """
    Uses Gemini to evaluate how well a student matches an opportunity.
    Uses the FULL CV text + brain dump for more accurate evaluation.
    
    Returns a dict with 'score' (0-100), 'reason' (string), and 'is_eligible' (boolean).
    """
    # Build student context from raw texts
    student_context = f"CV COMPLETO:\n{cv_raw_text[:6000]}"  # Truncate for Gemini context
    if brain_dump_text and brain_dump_text.strip():
        student_context += f"\n\nCONTEXTO ADICIONAL DEL ESTUDIANTE:\n{brain_dump_text.strip()[:2000]}"
    
    prompt = f"""Eres un asesor académico experto. Evalúa si este estudiante es un BUEN CANDIDATO para esta oportunidad.

{student_context}

OPORTUNIDAD:
{json.dumps(opportunity, ensure_ascii=False, indent=2)}

EVALÚA CON ESTOS CRITERIOS PONDERADOS:
1. ELEGIBILIDAD (40%): ¿El estudiante cumple los requisitos básicos?
   - ¿Su nivel de estudios es compatible con la oportunidad?
   - ¿Su país es elegible o la oportunidad es internacional?
   - ¿Su carrera/experiencia es relevante?
   
2. ALINEACIÓN DE INTERESES (30%): ¿Los intereses y ambiciones del estudiante coinciden con el enfoque de la oportunidad?

3. HABILIDADES (20%): ¿Las habilidades y experiencia del estudiante son relevantes?

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
        
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        if 'score' not in result:
            return {"score": 0, "reason": "Invalid response format from AI", "description": "", "is_eligible": False}
        
        score = int(result['score'])
        score = max(0, min(100, score))
        
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
    Main logic: Fetches student (including raw texts), gets opportunities using
    full CV text, scores them, and saves matches.
    """
    try:
        # 1. Fetch the student row (now including cv_raw_text and brain_dump_text)
        response = supabase.table("students").select("*").eq("id", student_id).execute()
        
        if not response.data or len(response.data) == 0:
            print(f"No student found with ID: {student_id}")
            return {"error": "Student not found"}
        
        student_row = response.data[0]
        
        # 2. Extract raw texts for search and evaluation
        cv_raw_text = student_row.get('cv_raw_text', '') or ''
        brain_dump_text = student_row.get('brain_dump_text', '') or ''
        
        # 3. Also get profile_data as fallback
        profile_data = student_row.get('profile_data', {})
        if isinstance(profile_data, str):
            try:
                profile_data = json.loads(profile_data)
            except:
                profile_data = {}

        print(f"Processing matches for student: {student_row.get('name', 'Unknown')}")
        print(f"CV text length: {len(cv_raw_text)} chars | Brain dump: {'Yes' if brain_dump_text else 'No'}")


########################################
#########   SOLO ES TEMPORAL   #########
########################################
        # 4. Search using FULL raw texts - Elegir entre Gemini (temporal) o Perplexity (real)
        if USE_GEMINI_FOR_SEARCH:
            opportunities = search_opportunities_with_gemini(
                cv_raw_text=cv_raw_text,
                brain_dump_text=brain_dump_text,
                profile_data=profile_data,
                num_results=num_results
            )
        else:
            opportunities = search_opportunities_with_perplexity(
                cv_raw_text=cv_raw_text,
                brain_dump_text=brain_dump_text,
                profile_data=profile_data,
                num_results=num_results
            )
########################################
#########   SOLO ES TEMPORAL   #########      
########################################

        print(f"Found {len(opportunities)} opportunities to evaluate")
        
        matches_saved = 0
        
        # 5. Evaluate and Save using full texts
        for opportunity in opportunities:
            if not isinstance(opportunity, dict):
                print(f"Skipping invalid opportunity: {opportunity}")
                continue
            
            title = opportunity.get('title', 'Unknown Position')
            print(f"\nEvaluating: {title}")
            
            # Score with Gemini using full CV text
            evaluation = evaluate_match(cv_raw_text, brain_dump_text, opportunity, profile_data)
            score = evaluation['score']
            reason = evaluation['reason']
            description = evaluation.get('description', '')
            is_eligible = evaluation.get('is_eligible', True)
            eligibility_notes = evaluation.get('eligibility_notes', '')
            
            deadline_info = opportunity.get('deadline_info', '')
            
            print(f"Score: {score}/100 | Eligible: {is_eligible} - {reason}")
            
            if is_eligible and score >= 50:
                try:
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
