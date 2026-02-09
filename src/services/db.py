"""
Database service for Novo (Supabase).

Expects the following environment variables:
- SUPABASE_URL
- SUPABASE_KEY
"""

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from supabase import Client, create_client
from datetime import datetime, timezone


# Load environment variables from .env if present
load_dotenv()


def _get_supabase_client() -> Client:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_KEY") or "").strip()

    if not url or not key:
        raise ValueError(
            "Supabase credentials missing. Please set SUPABASE_URL and SUPABASE_KEY in your environment/.env."
        )

    return create_client(url, key)


_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = _get_supabase_client()
    return _client


def save_student_profile(ai_result_json: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Inserts a row into `students` table:
      - name: ai_result_json["name"]
      - profile_data: full ai_result_json (jsonb)
      - user_id: UUID of authenticated user (REQUIRED after migration)

    Returns the inserted row (as dict) when available.
    """
    name = (ai_result_json.get("name") or "Unknown").strip()

    if not user_id:
        raise ValueError("user_id is required to save a student profile")

    payload = {
        "name": name,
        "profile_data": ai_result_json,
        "user_id": user_id
    }

    # Insert and return inserted row
    res = (
        get_client()
        .table("students")
        .insert(payload)
        .execute()
    )

    # supabase-py returns `.data` (list of rows)
    data = getattr(res, "data", None)
    if isinstance(data, list) and data:
        return data[0]
    return payload


def get_student_profiles_by_user(user_id: str) -> list:
    """
    Get all student profiles for a specific user
    
    Args:
        user_id: UUID of the authenticated user
        
    Returns:
        list: List of student profiles belonging to this user
    """
    try:
        response = get_client().table("students").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting student profiles: {e}")
        return []


def get_latest_student_profile_by_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the most recent student profile for a user
    
    Args:
        user_id: UUID of the authenticated user
        
    Returns:
        dict: Most recent student profile or None
    """
    try:
        response = (
            get_client()
            .table("students")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error getting latest profile: {e}")
        return None


def get_student_profile_by_id(student_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific student profile, ensuring it belongs to the user
    
    Args:
        student_id: ID of the student profile
        user_id: UUID of the authenticated user
        
    Returns:
        dict: Student profile or None if not found or doesn't belong to user
    """
    try:
        response = (
            get_client()
            .table("students")
            .select("*")
            .eq("id", student_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        return response.data if response.data else None
    except Exception as e:
        print(f"Error getting student profile: {e}")
        return None


def get_matches_for_student(student_id: str, user_id: str) -> list:
    """
    Get matches for a specific student profile
    """
    try:
        # First verify the profile belongs to the user
        profile = get_student_profile_by_id(student_id, user_id)
        if not profile:
            return []
            
        response = (
            get_client()
            .table("matches")
            .select("*")
            .eq("student_id", student_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting matches: {e}")
        return []

def update_student_profile_data(student_id: str, updated_data: Dict[str, Any], user_id: str) -> bool:
    """
    Update the JSON profile data for a student.
    
    Args:
        student_id: ID of the student profile
        updated_data: Dictionary of data to update/merge into profile_data
        user_id: ID of the user owning the profile (for security)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # First verify existence and ownership
        # We need to fetch the current profile first to merge the data, 
        # or we can rely on the frontend sending the full structure.
        # The prompt implies updating specific fields (top_skills, ambitions).
        # Depending on how jsonb update works in supabase-py/postgres, 
        # normally a patch update to a jsonb column might require specific syntax 
        # or fetching the whole object, modifying it, and saving it back.
        
        # Let's fetch the current profile first to be safe and ensure we don't overwrite everything else.
        current_profile = get_student_profile_by_id(student_id, user_id)
        if not current_profile:
            return False
            
        current_data = current_profile.get('profile_data', {})
        if not isinstance(current_data, dict):
            current_data = {}
            
        # Merge updated_data into current_data
        # This is a shallow merge. If deeper merge is needed, logic should be adjusted.
        for key, value in updated_data.items():
            current_data[key] = value
            
        # Update the record
        client = get_client()
        response = (
            client
            .table("students")
            .update({"profile_data": current_data})
            .eq("id", student_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        # Check if update was successful (response should contain data)
        return bool(response.data)
        
    except Exception as e:
        print(f"Error updating student profile: {e}")
        return False




def verify_student_ownership(student_id: str, user_id: str) -> bool:
    """
    Verify that a student profile belongs to a specific user
    
    Args:
        student_id: ID of the student profile
        user_id: UUID of the authenticated user
        
    Returns:
        bool: True if student belongs to user, False otherwise
    """
    try:
        response = (
            get_client()
            .table("students")
            .select("id")
            .eq("id", student_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(response.data)
    except Exception as e:
        print(f"Error verifying ownership: {e}")
        return False

#New Code For Premium Features
    
def get_student_usage_info(student_id: str) -> Dict[str, Any]:
    """Obtiene estado premium y última búsqueda."""
    try:
        response = get_client().table("students").select("is_premium, last_search_at").eq("id", student_id).single().execute()
        data = response.data if response.data else {}
        return {
            "is_premium": data.get("is_premium", False),
            "last_search_at": data.get("last_search_at")
        }
    except Exception as e:
        print(f"Error usage info: {e}")
        return {"is_premium": False, "last_search_at": None}

def update_last_search_date(student_id: str) -> None:
    """Marca la fecha actual como última búsqueda."""
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        get_client().table("students").update({"last_search_at": now_iso}).eq("id", student_id).execute()
    except Exception as e:
        print(f"Error updating search date: {e}")

def is_user_premium(user_id: str) -> bool:
    """Verifica si el usuario tiene algún perfil con is_premium=True."""
    if not user_id:
        return False
    try:
        response = get_client().table("students").select("is_premium").eq("user_id", user_id).eq("is_premium", True).limit(1).execute()
        return len(response.data) > 0 if response.data else False
    except Exception as e:
        print(f"Error checking premium status: {e}")
        return False




def set_student_premium(student_id: str, is_premium: bool = True) -> bool:
    """
    Sets the premium status for a student.
    
    Args:
        student_id: ID of the student profile
        is_premium: Boolean status to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = (
            get_client()
            .table("students")
            .update({"is_premium": is_premium})
            .eq("id", student_id)
            .execute()
        )
        return bool(response.data)
    except Exception as e:
        print(f"Error setting premium status: {e}")
        return False
