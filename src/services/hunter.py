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

def search_opportunities_with_perplexity(profile_data):
    """
    Uses Perplexity to find real opportunities (internships, fellowships, programs, research positions, etc.) based on profile.
    """
    print("🔎 Asking Perplexity to search for opportunities...")
    
    # Extract the most important data: ambitions, goals, and summary
    ambitions = profile_data.get('ambitions', '')
    career_goals = profile_data.get('career_goals', '')
    summary = profile_data.get('summary', '')
    interests = profile_data.get('interests', [])
    
    # Skills are secondary - only use if ambitions are missing
    skills = profile_data.get('top_skills', ['General Tech'])
    
    # Build a query focused on what the student WANTS, not just what they know
    if ambitions or career_goals or summary:
        # Prioritize their goals and ambitions
        goal_text = f"{ambitions} {career_goals} {summary}".strip()
        interest_text = " ".join(interests[:3]) if interests else ""
        search_query = f"{goal_text} {interest_text} oportunidades becas programas investigación pasantías estudiantes 2026"
    else:
        # Fallback to skills if no ambitions are provided
        search_query = f"{skills[0]} oportunidades becas programas investigación pasantías estudiantes 2026"
    
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un extractor de datos estructurados. Tu ÚNICA tarea es buscar 3 oportunidades REALES Y ESPECÍFICAS para estudiantes universitarios "
                    "(pasantías, becas, programas de investigación, intercambios, concursos, etc.) que se alineen con sus OBJETIVOS PROFESIONALES y AMBICIONES. \n"
                    "Céntrate en encontrar oportunidades que coincidan con lo que el estudiante QUIERE LOGRAR y sus ASPIRACIONES, no solo sus habilidades técnicas actuales. "
                    "Busca oportunidades que les ayuden a alcanzar sus metas, explorar sus intereses y alinearse con su visión de carrera. \n\n"
                    "Debes devolver SOLO un objeto JSON sin procesar. No escribas texto introductorio. \n"
                    "El contenido de los campos (title, company, description, etc.) DEBE estar en ESPAÑOL.\n"
                    "Usa este esquema exacto:\n"
                    "[\n"
                    "  {\n"
                    "    \"title\": \"Título de la Oportunidad Aquí\",\n"
                    "    \"company\": \"Nombre de la Organización/Institución\",\n"
                    "    \"location\": \"Ciudad, País o Remoto\",\n"
                    "    \"url\": \"https://link-to-opportunity.com\",\n"
                    "    \"description\": \"Una frase corta sobre la oportunidad en Español.\"\n"
                    "  }\n"
                    "]"
                )
            },
            {
                "role": "user",
                "content": f"Busca 3 oportunidades actuales para estudiantes universitarios basadas en sus metas y ambiciones: {search_query}"
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
    Returns a dict with 'score' (0-100) and 'reason' (string).
    """
    prompt = f"""Actúa como un asesor académico y de carrera. Compara este Perfil de Estudiante: {json.dumps(student_profile)} con esta Oportunidad (que podría ser una pasantía, beca, programa de investigación, intercambio o concurso): {json.dumps(opportunity)}. 
    
    Devuelve un JSON exacto con los siguientes campos:
    - 'score': (integer 0-100)
    - 'description': (string, una descripción breve de 1 o 2 frases sobre de qué trata el programa, en Español)
    - 'reason': (string, explicación breve de por qué hace match con el perfil del estudiante, en Español)
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
            return {"score": 0, "reason": "Invalid response format from AI", "description": ""}
        
        # Ensure score is an integer between 0 and 100
        score = int(result['score'])
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "description": result.get('description', ''),
            "reason": result.get('reason', '')
        }
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
        return {"score": 0, "reason": "Failed to parse AI response", "description": ""}
    
    except Exception as e:
        print(f"Error evaluating match: {e}")
        return {"score": 0, "reason": "Error during evaluation", "description": ""}


def find_and_save_matches(student_id):
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
        opportunities = search_opportunities_with_perplexity(profile_data)
        
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
            
            # Score with Gemini
            evaluation = evaluate_match(profile_data, opportunity)
            score = evaluation['score']
            reason = evaluation['reason']
            description = evaluation.get('description', '')
            
            print(f"Score: {score}/100 - {reason}")
            
            if score > 70:
                try:
                    # Combine description and reason to show both in the existing match_reason column
                    full_reason = f"{description}\n\n💡 Match: {reason}"

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
