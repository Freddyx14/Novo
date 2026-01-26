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
      - user_id: UUID of authenticated user (optional)

    Returns the inserted row (as dict) when available.
    """
    name = (ai_result_json.get("name") or "Unknown").strip()

    payload = {
        "name": name,
        "profile_data": ai_result_json,
    }
    
    # Add user_id if provided (for authenticated users)
    if user_id:
        payload["user_id"] = user_id

    # Insert and return inserted row
    res = (
        get_client()
        .table("students")
        .insert(payload)
        .execute()
    )

    # supabase-py returns `.data` (list of rows) and `.error` in older versions;
    # new versions raise on HTTP errors. We'll normalize to dict.
    data = getattr(res, "data", None)
    if isinstance(data, list) and data:
        return data[0]
    return payload

