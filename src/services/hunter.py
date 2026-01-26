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
    
    # 1. Extract simple keywords (Gemini is better at this, but we'll do a quick grab here)
    # If you have a 'top_skills' list, use the first one, else default to 'Software'
    skills = profile_data.get('top_skills', ['General Tech'])[0] 
    # Use a default location if none exists (or 'Remote')
    location = "Remote or Global" 
    
    # Construct a Google-like search query (Simple is better for Perplexity)
    search_query = f"{skills} opportunities fellowships programs research internships {location} students 2026"
    
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a structured data extractor. Your ONLY task is to search for 3 REAL, SPECIFIC opportunities for university students "
                    "(internships, fellowships, research programs, scholarships, exchange programs, competitions, etc.) found in the search results. \n"
                    "You must return ONLY a raw JSON object. Do not write any intro text. Do not say 'Here is the list'. \n"
                    "Use this exact schema:\n"
                    "[\n"
                    "  {\n"
                    "    \"title\": \"Opportunity Title Here\",\n"
                    "    \"company\": \"Organization/Institution Name\",\n"
                    "    \"location\": \"City, Country or Remote\",\n"
                    "    \"url\": \"https://link-to-opportunity.com\",\n"
                    "    \"description\": \"One short sentence about the opportunity.\"\n"
                    "  }\n"
                    "]"
                )
            },
            {
                "role": "user",
                "content": f"Search for 3 current opportunities for university students for this query: {search_query}"
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
    prompt = f"""Act as an academic and career advisor. Compare this Student Profile: {json.dumps(student_profile)} with this Opportunity (which could be an internship, fellowship, research program, scholarship, exchange program, or competition): {json.dumps(opportunity)}. Return a JSON with 'score' (0-100) and 'reason' (max 1 sentence)."""
    
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
        if 'score' not in result or 'reason' not in result:
            return {"score": 0, "reason": "Invalid response format from AI"}
        
        # Ensure score is an integer between 0 and 100
        score = int(result['score'])
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "reason": result['reason']
        }
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
        return {"score": 0, "reason": "Failed to parse AI response"}
    
    except Exception as e:
        print(f"Error evaluating match: {e}")
        return {"score": 0, "reason": "Error during evaluation"}


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
            
            print(f"Score: {score}/100 - {reason}")
            
            if score > 70:
                try:
                    match_data = {
                        "student_id": student_id,
                        "title": opportunity.get('title', 'Untitled'),
                        "company": opportunity.get('company', 'Unknown'),
                        "location": opportunity.get('location', 'Unknown'),
                        "match_score": score,
                        "match_reason": reason,
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
