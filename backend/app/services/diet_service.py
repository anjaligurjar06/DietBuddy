import httpx
import os
from datetime import date, datetime
from typing import Optional
from supabase import Client
from app.models.diet_model import DietEntryCreate, DietEntryUpdate

# CRUD helpers for diet entries
def create_diet_entry(supabase: Client, user_id: str, data: DietEntryCreate, token: str | None = None) -> dict:
    """Insert a new diet entry for today."""
    if token:
        supabase.postgrest.auth(token)

    payload = {
        "user_id": user_id,
        "breakfast": data.breakfast,
        "lunch": data.lunch,
        "dinner": data.dinner,
        "snacks": data.snacks,
    }
    try:
        response = supabase.table("diet_entries").insert(payload).execute()
    except Exception as exc:
        raise Exception(getattr(exc, "message", None) or repr(exc)) from exc

    if not response.data:
        raise Exception("Failed to create diet entry")
    return response.data[0]

def get_entries_by_user(supabase: Client, user_id: str) -> list[dict]:
    """Fetch all diet entries for frontend compatibility routes."""
    response = (
        supabase.table("diet_entries")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_today_entry(supabase: Client, user_id: str) -> Optional[dict]:
    """Fetch the diet entry created today for a user."""
    today_start = datetime.combine(date.today(), datetime.min.time()).isoformat()
    today_end   = datetime.combine(date.today(), datetime.max.time()).isoformat()

    response = (
        supabase.table("diet_entries")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", today_start)
        .lte("created_at", today_end)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def get_all_entries(supabase: Client, user_id: str, limit: int = 30) -> list[dict]:
    """Fetch recent diet entries for a user (default last 30)."""
    response = (
        supabase.table("diet_entries")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def update_diet_entry(supabase: Client, entry_id: str, user_id: str, data: DietEntryUpdate) -> dict:
    """Update an existing diet entry (only provided fields)."""
    values = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    payload = {k: v for k, v in values.items() if v is not None}
    if not payload:
        raise Exception("No fields provided to update")

    response = (
        supabase.table("diet_entries")
        .update(payload)
        .eq("id", entry_id)
        .eq("user_id", user_id)   
        .execute()
    )
    if not response.data:
        raise Exception("Entry not found or not authorised")
    return response.data[0]


def delete_diet_entry(supabase: Client, entry_id: str, user_id: str) -> bool:
    """Delete a diet entry (only if it belongs to the user)."""
    response = (
        supabase.table("diet_entries")
        .delete()
        .eq("id", entry_id)
        .eq("user_id", user_id)
        .execute()
    )
    return bool(response.data)


# AI Recommendation via OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL           = "meta-llama/llama-3-8b-instruct"

def _build_prompt(meals: dict) -> str:
    """Build a clear prompt from today's meals."""
    lines = []
    for meal, food in meals.items():
        if food:
            lines.append(f"  - {meal.capitalize()}: {food}")

    if not lines:
        meals_text = "  No meals logged yet today."
    else:
        meals_text = "\n".join(lines)

    return f"""You are a certified nutritionist and diet coach. A user has logged the following meals for today:

{meals_text}

Please provide:
1. A brief nutritional assessment of today's meals (2-3 sentences).
2. What nutrients might be missing or excessive.
3. 2-3 specific, practical recommendations for improvement tomorrow.
4. One healthy recipe idea that complements what they ate today.

Keep the tone friendly, motivating, and concise. Avoid generic advice."""


async def get_ai_recommendation(meals: dict) -> str:
    """
    Call OpenRouter API and return a recommendation string.
    `meals` should be a dict like {"breakfast": "...", "lunch": "...", ...}
    """
    if not OPENROUTER_API_KEY:
        raise Exception("OPENROUTER_API_KEY is not set in environment variables")

    prompt = _build_prompt(meals)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("APP_URL", "http://localhost:3000"),  
        "X-Title": "DietBuddy",
    }

    body = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful nutritionist assistant for an app called DietBuddy.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": 600,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"OpenRouter error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
