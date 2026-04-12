"""
Database service for Novo (Supabase).

Expects the following environment variables:
- SUPABASE_URL
- SUPABASE_KEY
"""

import os
import re
from typing import Any, Dict, Optional
from uuid import uuid4

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


def save_student_profile(ai_result_json: Dict[str, Any], user_id: Optional[str] = None, cv_raw_text: str = "", brain_dump_text: str = "", cv_file_path: str = "") -> Dict[str, Any]:
    """
    Inserts a row into `students` table:
      - name: ai_result_json["name"]
      - profile_data: full ai_result_json (jsonb)
      - user_id: UUID of authenticated user (REQUIRED after migration)
      - cv_raw_text: Raw text extracted from CV PDF
      - brain_dump_text: Raw text from user's brain dump input
      - cv_file_path: Path to the stored PDF file (optional, stored in profile_data)

    Returns the inserted row (as dict) when available.
    """
    name = (ai_result_json.get("name") or "Unknown").strip()

    if not user_id:
        raise ValueError("user_id is required to save a student profile")

    # Add cv_file_path to profile_data if provided
    if cv_file_path:
        ai_result_json['cv_file_path'] = cv_file_path

    payload = {
        "name": name,
        "profile_data": ai_result_json,
        "user_id": user_id,
        "cv_raw_text": cv_raw_text or "",
        "brain_dump_text": brain_dump_text or ""
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


def _extract_objective_id_from_reason(reason: str) -> Optional[str]:
    """Extract objective id marker from match_reason, e.g. [[OBJ_ID:abc-123]]."""
    if not reason:
        return None
    match = re.search(r"\[\[OBJ_ID:([^\]]+)\]\]", reason)
    return match.group(1) if match else None


def _extract_tag_value(reason: str, tag_name: str) -> Optional[str]:
    """Extract generic marker value from match_reason, e.g. [[TAG:value]]."""
    if not reason:
        return None
    pattern = rf"\[\[{re.escape(tag_name)}:([^\]]+)\]\]"
    match = re.search(pattern, reason)
    return match.group(1).strip() if match else None


def _strip_objective_markers(reason: str) -> str:
    """Remove internal metadata markers from match_reason before rendering."""
    if not reason:
        return ""
    return re.sub(r"\[\[[A-Z_]+:[^\]]+\]\]\s*", "", reason).strip()


def get_matches_for_student(
    student_id: str,
    user_id: str,
    objective_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> list:
    """
    Get matches for a specific student profile, optionally filtered by objective.
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
        matches = response.data if response.data else []

        filtered = []
        for match in matches:
            reason = match.get("match_reason") or ""
            tagged_objective_id = _extract_objective_id_from_reason(reason)
            eligibility_status = _extract_tag_value(reason, "ELIGIBILITY_STATUS")
            target_horizon = _extract_tag_value(reason, "TARGET_HORIZON")
            readiness_gap = _extract_tag_value(reason, "READINESS_GAP")

            if objective_id and tagged_objective_id != objective_id:
                continue

            normalized_status = eligibility_status or "eligible_now"
            if status_filter and status_filter != "all" and normalized_status != status_filter:
                continue

            clean_match = dict(match)
            clean_match["match_reason"] = _strip_objective_markers(reason)
            clean_match["objective_id"] = tagged_objective_id
            clean_match["eligibility_status"] = normalized_status
            clean_match["target_horizon"] = target_horizon
            clean_match["readiness_gap"] = readiness_gap
            filtered.append(clean_match)

        return filtered
    except Exception as e:
        print(f"Error getting matches: {e}")
        return []


def delete_matches_for_student(
    student_id: str,
    user_id: str,
    objective_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> int:
    """
    Delete matches for a student profile with optional objective/status filters.

    Returns:
        int: number of deleted matches
    """
    try:
        profile = get_student_profile_by_id(student_id, user_id)
        if not profile:
            return 0

        # If no filters are provided, do fast bulk delete.
        no_objective = not objective_id
        no_status = not status_filter or status_filter == "all"
        if no_objective and no_status:
            response = get_client().table("matches").delete().eq("student_id", student_id).execute()
            data = getattr(response, "data", None)
            return len(data) if isinstance(data, list) else 0

        matches = get_matches_for_student(
            student_id,
            user_id,
            objective_id=objective_id,
            status_filter=status_filter,
        )

        deleted = 0
        for match in matches:
            match_id = match.get("id")
            if not match_id:
                continue
            get_client().table("matches").delete().eq("id", match_id).eq("student_id", student_id).execute()
            deleted += 1

        return deleted
    except Exception as e:
        print(f"Error deleting matches with filters: {e}")
        return 0


def delete_old_matches_for_user(user_id: str, keep_student_id: str) -> bool:
    """
    Delete all matches for a user EXCEPT for the specified student profile.
    This is useful when creating a new profile to avoid showing matches from old profiles.
    
    Args:
        user_id: UUID of the authenticated user
        keep_student_id: Student ID to keep matches for (don't delete these)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get all student IDs for this user
        all_profiles = get_student_profiles_by_user(user_id)
        old_student_ids = [p['id'] for p in all_profiles if p['id'] != keep_student_id]
        
        if not old_student_ids:
            # No old profiles to clean
            return True
        
        # Delete matches for each old profile
        for student_id in old_student_ids:
            try:
                get_client().table("matches").delete().eq("student_id", student_id).execute()
                print(f"Deleted matches for old student profile: {student_id}")
            except Exception as e:
                print(f"Error deleting matches for student {student_id}: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error deleting old matches: {e}")
        return False


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


def get_search_objective_context(student_id: str, user_id: str) -> Dict[str, Any]:
    """
    Return objectives and active objective for a student profile.
    Stored in students.profile_data as:
      - search_objectives: list[dict]
      - active_search_objective_id: str
    """
    try:
        profile = get_student_profile_by_id(student_id, user_id)
        if not profile:
            return {"objectives": [], "active_objective": None, "active_objective_id": None}

        profile_data = profile.get("profile_data") or {}
        if not isinstance(profile_data, dict):
            profile_data = {}

        raw_objectives = profile_data.get("search_objectives") or []
        objectives = [o for o in raw_objectives if isinstance(o, dict) and o.get("id") and o.get("name")]

        active_id = profile_data.get("active_search_objective_id")
        if not active_id and objectives:
            active_id = objectives[0].get("id")

        active_objective = next((o for o in objectives if o.get("id") == active_id), None)

        return {
            "objectives": objectives,
            "active_objective": active_objective,
            "active_objective_id": active_id,
        }
    except Exception as e:
        print(f"Error getting objective context: {e}")
        return {"objectives": [], "active_objective": None, "active_objective_id": None}


def create_search_objective(student_id: str, user_id: str, objective_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create and persist a new search objective for a student profile."""
    try:
        profile = get_student_profile_by_id(student_id, user_id)
        if not profile:
            return None

        profile_data = profile.get("profile_data") or {}
        if not isinstance(profile_data, dict):
            profile_data = {}

        objectives = profile_data.get("search_objectives") or []
        if not isinstance(objectives, list):
            objectives = []

        objective_name = (objective_data.get("name") or "").strip()
        if not objective_name:
            return None

        new_objective = {
            "id": str(uuid4()),
            "name": objective_name,
            "type": (objective_data.get("type") or "general").strip(),
            "keywords": (objective_data.get("keywords") or "").strip(),
            "location": (objective_data.get("location") or "").strip(),
            "level": (objective_data.get("level") or "").strip(),
            "notes": (objective_data.get("notes") or "").strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        objectives.append(new_objective)
        profile_data["search_objectives"] = objectives

        if not profile_data.get("active_search_objective_id"):
            profile_data["active_search_objective_id"] = new_objective["id"]

        response = (
            get_client()
            .table("students")
            .update({"profile_data": profile_data})
            .eq("id", student_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            return None

        return new_objective
    except Exception as e:
        print(f"Error creating search objective: {e}")
        return None


def set_active_search_objective(student_id: str, user_id: str, objective_id: str) -> bool:
    """Set the active objective for a student profile."""
    try:
        profile = get_student_profile_by_id(student_id, user_id)
        if not profile:
            return False

        profile_data = profile.get("profile_data") or {}
        if not isinstance(profile_data, dict):
            return False

        objectives = profile_data.get("search_objectives") or []
        if not isinstance(objectives, list):
            return False

        exists = any(isinstance(o, dict) and o.get("id") == objective_id for o in objectives)
        if not exists:
            return False

        profile_data["active_search_objective_id"] = objective_id

        response = (
            get_client()
            .table("students")
            .update({"profile_data": profile_data})
            .eq("id", student_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(response.data)
    except Exception as e:
        print(f"Error setting active objective: {e}")
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
