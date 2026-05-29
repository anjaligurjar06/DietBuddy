import os
import jwt
from datetime import datetime, timedelta
from app.core.supabase import supabase
from app.utils.hash import hash_password, verify_password

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# Helper function to create JWT token for a user
def _create_token(user_id: str, email: str) -> str:
    payload = {
        "id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# Public functions for user management
def create_user(user):
    user_dict = user.dict()
    user_dict["password"] = hash_password(user_dict["password"])
    data = supabase.table("users").insert(user_dict).execute()
    if not data.data:
        return {"error": "Failed to create user"}
    created = data.data[0]
    token = _create_token(created["id"], created["email"])
    return {
        "message": "User created successfully",
        "token": token,
        "data": created,
    }

def login_user(email: str, password: str):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if not res.data:
        return {"error": "Invalid email or password"}

    user = res.data[0]
    if not verify_password(password, user["password"]):
        return {"error": "Invalid email or password"}

    token = _create_token(user["id"], user["email"])
    return {
        "message": "Login successful",
        "token": token,
        "user": {k: v for k, v in user.items() if k != "password"},
    }


def get_supabase_auth_user(token: str) -> dict:
    """Return the Supabase Auth user for a frontend session token."""
    try:
        auth_response = supabase.auth.get_user(token)
        user = auth_response.user
        if user:
            return {
                "id": user.id,
                "email": user.email,
                "metadata": getattr(user, "user_metadata", {}) or {},
            }
    except Exception:
        pass
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "metadata": payload.get("user_metadata") or {},
        }
    except Exception:
        return {"id": None, "email": None}


def save_profile(profile, token: str):
    auth_user = get_supabase_auth_user(token)
    if not auth_user.get("id") or auth_user["id"] != profile.user_id:
        return {"error": "Invalid user token"}

    profile_dict = profile.model_dump() if hasattr(profile, "model_dump") else profile.dict()
    if auth_user.get("email"):
        profile_dict["email"] = auth_user["email"]

    attempts = [
        (profile_dict, "user_id"),
        ({**profile_dict, "id": profile.user_id}, "id"),
    ]
    for payload, conflict_column in attempts:
        try:
            if conflict_column == "id":
                payload.pop("user_id", None)
            data = supabase.table("users").upsert(payload, on_conflict=conflict_column).execute()
            if data.data:
                return {
                    "message": "Profile saved successfully",
                    "data": data.data[0],
                }
        except Exception:
            continue

    return {"error": "Profile save failed"}


def get_profile(user_id: str, token: str | None = None):
    auth_user = get_supabase_auth_user(token) if token else {"metadata": {}}
    if token:
        supabase.postgrest.auth(token)

    profile = None
    for column in ("user_id", "id"):
        try:
            data = supabase.table("users").select("*").eq(column, user_id).limit(1).execute()
            if data.data:
                profile = data.data[0]
                break
        except Exception:
            continue

    if not profile:
        metadata = auth_user.get("metadata") or {}
        return {
            "message": "Profile not found; using defaults",
            "data": {
                "id": user_id,
                "name": metadata.get("name", ""),
                "age": metadata.get("age"),
                "gender": metadata.get("gender", ""),
                "height": metadata.get("height"),
                "weight": metadata.get("weight"),
                "diet": metadata.get("diet") or "Vegetarian",
                "goal": metadata.get("goal") or "Maintain Weight",
                "activity": metadata.get("activity") or "Low",
                "health": metadata.get("health", ""),
                "allergies": metadata.get("allergies", ""),
            },
        }

    profile.pop("password", None)
    return {
        "message": "Profile retrieved successfully",
        "data": profile,
    }
