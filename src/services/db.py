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
    Get all matches for a student, ensuring the student belongs to the user
    
    Args:
        student_id: ID of the student profile
        user_id: UUID of the authenticated user
        
    Returns:
        list: List of matches or empty list
    """
    try:
        # First verify the student belongs to the user
        student = get_student_profile_by_id(student_id, user_id)
        if not student:
            return []
        
        # Get matches for this student
        response = (
            get_client()
            .table("matches")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting matches: {e}")
        return []


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

