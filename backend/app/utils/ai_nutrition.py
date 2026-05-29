"""
ai_nutrition.py  —  DietBuddy
Utility wrappers around the OpenRouter API for nutrition intelligence.
"""

import httpx
import os
import json
import re
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(proxy_var, None)

OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "meta-llama/llama-3-8b-instruct")


# Internal helper functions (not directly related to nutrition logic, but to API calls and JSON handling)
async def _call_openrouter(system_prompt: str, user_prompt: str, max_tokens: int = 600, json_mode: bool = False) -> str:
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  os.getenv("APP_URL", "http://localhost:3000"),
        "X-Title":       "DietBuddy",
    }

    body = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens":  max_tokens,
        "temperature": 0.2 if json_mode else 0.7,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
        resp = await client.post(OPENROUTER_URL, headers=headers, json=body)

    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter {resp.status_code}: {resp.text}")

    return resp.json()["choices"][0]["message"]["content"].strip()


def _json_from_model_text(raw: str):
    clean = raw.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean)

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r"(\[.*\]|\{.*\})", clean, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(1))


async def _repair_json(raw: str) -> dict:
    system = (
        "You repair malformed JSON. Respond ONLY with one valid JSON object. "
        "No markdown, no explanation."
    )
    user = f"""Repair this into valid JSON with this exact shape:
{{"recommendations":[{{"food_name":"string","calories":0,"protein":0,"carbs":0,"fats":0,"reason":"string"}}]}}

Malformed content:
{raw}"""
    repaired = await _call_openrouter(system, user, max_tokens=700, json_mode=True)
    data = _json_from_model_text(repaired)
    if not isinstance(data, dict):
        raise ValueError("Repaired recommendation response was not an object")
    return data

# Public helper Fuctions
async def analyze_meals(meals: dict) -> str:
    """Full nutritional analysis + next-day recommendations."""
    lines = [f"  - {k.capitalize()}: {v}" for k, v in meals.items() if v]
    meal_text = "\n".join(lines) if lines else "  No meals logged."

    system = "You are a certified nutritionist assistant for DietBuddy app."
    user   = f"""Today's meals:
{meal_text}

Give:
1. Brief nutritional assessment (2-3 sentences).
2. Missing or excessive nutrients.
3. 2-3 practical improvement tips for tomorrow.
4. One healthy recipe idea that complements today's meals.

Be friendly, concise, and specific."""

    return await _call_openrouter(system, user, max_tokens=600)


async def analyze_single_food(food_name: str) -> str:
    """Quick nutrition breakdown for a single food item (returns plain text)."""
    system = "You are a nutrition expert. Give brief, accurate food facts."
    user   = f"""Give a quick nutrition breakdown for: {food_name}

Include: approximate calories per serving, key macros (protein/carbs/fat),
top 3 micronutrients, and one health benefit. Keep it under 150 words."""

    return await _call_openrouter(system, user, max_tokens=300)


async def get_nutrition(food_name: str, grams: float) -> dict:
    """
    Returns macro breakdown as a dict for food_service.py to store in DB.
    Asks the model to respond in JSON so we can parse it reliably.

    Returns: {"calories": float, "protein": float, "carbs": float, "fats": float}
    """
    system = (
        "You are a nutrition database. Respond ONLY with a valid JSON object. "
        "No markdown, no explanation, no backticks."
    )
    user = (
        f"Give the nutrition for {grams}g of {food_name}. "
        "Return JSON with exactly these keys: calories, protein, carbs, fats. "
        "All values must be numbers (floats)."
    )

    raw = await _call_openrouter(system, user, max_tokens=100)

    try:
        data = _json_from_model_text(raw)
        return {
            "calories": float(data.get("calories", 0)),
            "protein":  float(data.get("protein",  0)),
            "carbs":    float(data.get("carbs",    0)),
            "fats":     float(data.get("fats",     0)),
        }
    except (json.JSONDecodeError, KeyError, ValueError):
        # Fallback: return zeros rather than crashing the whole request
        return {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fats": 0.0}


async def get_food_recommendations(context: dict) -> list[dict]:
    """
    Return 5 food recommendations as JSON objects.
    Each recommendation respects the user's diet preference.
    """
    diet = context.get("diet") or "Non-Vegetarian"
    today_foods = context.get("today_foods") or []
    today_meals = context.get("today_meals") or {}
    totals = context.get("totals") or {}
    profile = context.get("profile") or {}

    system = (
        "You are a nutrition recommendation engine for DietBuddy. "
        "Respond ONLY with one valid JSON object. No markdown, no explanation, no backticks. "
        "Every item must strictly follow the user's diet preference. "
        "Do not include UUIDs or database ids."
    )
    user = f"""User profile:
- Diet preference: {diet}
- Goal: {profile.get("goal", "Maintain Weight")}
- Activity: {profile.get("activity", "Low")}
- Health conditions: {profile.get("health", "None")}
- Allergies: {profile.get("allergies", "None")}

Today's meal text:
{json.dumps(today_meals, ensure_ascii=False)}

Today's food tracker entries:
{json.dumps(today_foods, ensure_ascii=False)}

Today's totals:
{json.dumps(totals, ensure_ascii=False)}

Recommend exactly 5 foods for the rest of today or tomorrow.
Rules:
- If diet is Vegetarian, do not include meat, chicken, fish, seafood, or eggs.
- If diet is Vegan, do not include meat, chicken, fish, seafood, eggs, milk, paneer, curd, yogurt, cheese, ghee, or honey.
- If diet is Non-Vegetarian, any normal food is allowed unless allergies say otherwise.
- Avoid anything listed in allergies.
- Make the recommendations useful based on what the user already ate and their macros.

Return one JSON object with this exact shape:
{{"recommendations":[{{"food_name":"...", "calories":0, "protein":0, "carbs":0, "fats":0, "reason":"..."}}]}}
calories/protein/carbs/fats must be numbers for 100g serving."""

    raw = await _call_openrouter(system, user, max_tokens=700, json_mode=True)

    try:
        data = _json_from_model_text(raw)
    except json.JSONDecodeError:
        data = await _repair_json(raw)

    if isinstance(data, dict):
        data = data.get("recommendations", [])
    if not isinstance(data, list):
        raise ValueError("Recommendation response did not contain a recommendations list")

    recommendations = []
    for index, item in enumerate(data[:5], start=1):
        recommendations.append({
            "id": index,
            "food_name": str(item.get("food_name") or "Recommended food"),
            "calories": float(item.get("calories") or 0),
            "protein": float(item.get("protein") or 0),
            "carbs": float(item.get("carbs") or 0),
            "fats": float(item.get("fats") or 0),
            "reason": str(item.get("reason") or "Fits your current nutrition pattern."),
        })

    return recommendations


async def suggest_meal_plan(
    goal: str,
    dietary_preference: Optional[str] = None,
    allergies: Optional[str] = None,
) -> str:
    """Generate a 1-day meal plan tailored to a user's goal."""
    pref_line    = f"Dietary preference: {dietary_preference}" if dietary_preference else ""
    allergy_line = f"Allergies/avoid: {allergies}" if allergies else ""
    extras = "\n".join(filter(None, [pref_line, allergy_line]))

    system = "You are a meal planning expert for DietBuddy, an Indian health app."
    user   = f"""Create a 1-day Indian meal plan for goal: {goal}.
{extras}

Format:
- Breakfast: ...
- Mid-morning snack: ...
- Lunch: ...
- Evening snack: ...
- Dinner: ...

Add a one-line reason for each choice. Keep it practical and achievable."""

    return await _call_openrouter(system, user, max_tokens=500)
