from app.core.supabase import supabase
from app.services.auth_service import get_supabase_auth_user
from app.utils.ai_nutrition import get_food_recommendations, get_nutrition
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

# A list of fallback foods with nutrition info and tags for contextual recommendations when AI is unavailable.
FALLBACK_FOODS = [
    {"food_name": "Grilled Chicken Breast", "calories": 165, "protein": 31, "carbs": 0, "fats": 3.6, "diets": ["Non-Vegetarian"], "tags": ["protein", "low_carb"]},
    {"food_name": "Egg Bhurji", "calories": 155, "protein": 13, "carbs": 2, "fats": 11, "diets": ["Non-Vegetarian"], "tags": ["protein", "low_carb"]},
    {"food_name": "Tuna Salad", "calories": 132, "protein": 24, "carbs": 4, "fats": 2, "diets": ["Non-Vegetarian"], "tags": ["protein", "low_fat"]},
    {"food_name": "Paneer Bhurji", "calories": 220, "protein": 16, "carbs": 7, "fats": 15, "diets": ["Vegetarian", "Non-Vegetarian"], "tags": ["protein", "fat"]},
    {"food_name": "Greek Yogurt", "calories": 97, "protein": 9, "carbs": 3.6, "fats": 5, "diets": ["Vegetarian", "Non-Vegetarian"], "tags": ["protein", "light"]},
    {"food_name": "Moong Dal Chilla", "calories": 128, "protein": 8, "carbs": 18, "fats": 3, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["protein", "carbs"]},
    {"food_name": "Tofu Stir Fry", "calories": 144, "protein": 15, "carbs": 5, "fats": 8, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["protein", "low_carb"]},
    {"food_name": "Chickpea Salad", "calories": 164, "protein": 9, "carbs": 27, "fats": 2.6, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["protein", "carbs", "fiber"]},
    {"food_name": "Rajma Bowl", "calories": 140, "protein": 8, "carbs": 24, "fats": 1.5, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["protein", "carbs", "fiber"]},
    {"food_name": "Dal Khichdi", "calories": 180, "protein": 8, "carbs": 32, "fats": 3, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["carbs", "balanced"]},
    {"food_name": "Brown Rice", "calories": 216, "protein": 5, "carbs": 45, "fats": 1.8, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["carbs"]},
    {"food_name": "Sweet Potato Chaat", "calories": 86, "protein": 1.6, "carbs": 20, "fats": 0.1, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["carbs", "low_fat"]},
    {"food_name": "Sprouts Chaat", "calories": 120, "protein": 8, "carbs": 20, "fats": 1.5, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["protein", "light", "fiber"]},
    {"food_name": "Avocado", "calories": 160, "protein": 2, "carbs": 9, "fats": 15, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["fat"]},
    {"food_name": "Peanut Chutney", "calories": 190, "protein": 7, "carbs": 8, "fats": 16, "diets": ["Vegetarian", "Non-Vegetarian", "Vegan"], "tags": ["fat", "protein"]},
]
# Helper functions for diet enforcement and contextual fallback recommendations when AI is unavailable or to supplement AI suggestions.
def _today_range():
    return (
        datetime.combine(date.today(), datetime.min.time()).isoformat(),
        datetime.combine(date.today(), datetime.max.time()).isoformat(),
    )

# Nutrition totals calculation for a list of food entries, used to inform recommendation logic.
def _totals(entries: list[dict]) -> dict:
    return {
        "calories": sum(float(item.get("calories") or 0) for item in entries),
        "protein": sum(float(item.get("protein") or 0) for item in entries),
        "carbs": sum(float(item.get("carbs") or 0) for item in entries),
        "fats": sum(float(item.get("fats") or 0) for item in entries),
    }

# Diet normalization to standard categories for consistent recommendation logic.
def _normalize_diet(diet: str) -> str:
    diet_text = (diet or "Vegetarian").strip().lower()
    if "vegan" in diet_text:
        return "Vegan"
    if "veg" in diet_text and "non" not in diet_text:
        return "Vegetarian"
    return "Non-Vegetarian"

# Diet check logic to filter AI recommendations based on user's diet preference and already logged foods for the day.
def _is_allowed_for_diet(food_name: str, diet: str) -> bool:
    name = food_name.lower()
    non_veg_terms = [
        "chicken", "egg", "fish", "tuna", "salmon", "prawn", "shrimp",
        "seafood", "mutton", "beef", "pork", "lamb", "turkey", "meat",
        "liver", "ham", "bacon", "sausage",
    ]
    dairy_terms = ["milk", "paneer", "curd", "yogurt", "yoghurt", "cheese", "ghee", "butter", "honey"]

    if diet in ("Vegetarian", "Vegan") and any(term in name for term in non_veg_terms):
        return False
    if diet == "Vegan" and any(term in name for term in dairy_terms):
        return False
    return True

# Enforce diet and remove already logged foods from AI recommendations, then supplement with contextual fallback if needed to ensure a robust recommendation list.
def _enforce_diet(recommendations: list[dict], context: dict) -> list[dict]:
    diet = _normalize_diet(context.get("diet"))
    logged_names = {
        str(item.get("food_name", "")).strip().lower()
        for item in context.get("today_foods") or []
    }
    clean = []

    for item in recommendations:
        food_name = str(item.get("food_name") or "").strip()
        if not food_name or food_name.lower() in logged_names:
            continue
        if _is_allowed_for_diet(food_name, diet):
            clean.append(item)

    fallback = _contextual_fallback(context)
    seen = {item["food_name"].lower() for item in clean}
    for item in fallback:
        if len(clean) >= 5:
            break
        if item["food_name"].lower() not in seen and _is_allowed_for_diet(item["food_name"], diet):
            clean.append(item)
            seen.add(item["food_name"].lower())

    return [
        {**item, "id": index}
        for index, item in enumerate(clean[:5], start=1)
    ]

# Fallback reason generation based on which macros the food item can help with, and the user's current gaps and totals for the day.
def _fallback_reason(item: dict, totals: dict, target: dict) -> str:
    protein_gap = target["protein"] - totals.get("protein", 0)
    carb_gap = target["carbs"] - totals.get("carbs", 0)
    fat_gap = target["fats"] - totals.get("fats", 0)

    if "protein" in item["tags"] and protein_gap > 15:
        return "Helps close your protein gap based on today's tracker."
    if "carbs" in item["tags"] and carb_gap > 40:
        return "Adds steady carbs because today's logged carbs look low."
    if "fat" in item["tags"] and fat_gap > 15:
        return "Adds healthy fats to balance your current macro split."
    if "light" in item["tags"] and totals.get("calories", 0) > target["calories"] * 0.75:
        return "A lighter option for the rest of the day."
    return "Fits your diet preference and balances today's food log."

# Contextual fallback recommendation logic that scores a predefined list of foods based on the user's current macro gaps, diet, and already logged foods for the day to provide relevant suggestions when AI recommendations are unavailable.
def _contextual_fallback(context: dict) -> list[dict]:
    diet = _normalize_diet(context.get("diet"))
    totals = context.get("totals") or {}
    profile = context.get("profile") or {}
    logged_names = {
        str(item.get("food_name", "")).strip().lower()
        for item in context.get("today_foods") or []
    }

    goal = str(profile.get("goal") or "").lower()
    calorie_target = 1800
    if "gain" in goal:
        calorie_target = 2300
    elif "lose" in goal:
        calorie_target = 1600

    target = {
        "calories": calorie_target,
        "protein": 110 if diet == "Non-Vegetarian" else 85,
        "carbs": 230,
        "fats": 60,
    }

    protein_gap = target["protein"] - totals.get("protein", 0)
    carb_gap = target["carbs"] - totals.get("carbs", 0)
    fat_gap = target["fats"] - totals.get("fats", 0)
    calorie_gap = target["calories"] - totals.get("calories", 0)

    scored = []
    for item in FALLBACK_FOODS:
        if diet not in item["diets"] or item["food_name"].lower() in logged_names:
            continue

        score = 0.0
        if protein_gap > 0:
            score += item["protein"] * min(protein_gap / 25, 2)
        if carb_gap > 0:
            score += item["carbs"] * min(carb_gap / 60, 1.5) * 0.35
        if fat_gap > 0:
            score += item["fats"] * min(fat_gap / 20, 1.5) * 0.45
        if calorie_gap < 350:
            score -= item["calories"] * 0.04
        if "fiber" in item["tags"]:
            score += 4
        if "light" in item["tags"]:
            score += 3

        scored.append((score, item))

    recommendations = []
    for index, (_, item) in enumerate(sorted(scored, reverse=True, key=lambda row: row[0])[:5], start=1):
        recommendations.append({
            "id": index,
            "food_name": item["food_name"],
            "calories": item["calories"],
            "protein": item["protein"],
            "carbs": item["carbs"],
            "fats": item["fats"],
            "reason": _fallback_reason(item, totals, target),
        })

    return recommendations

# --- IGNORE ---
async def add_food(user_id: str, food_name: str, grams: float, token: str | None = None):
    """Fetch nutrition via AI then persist to DB. Must be awaited."""
    if token:
        supabase.postgrest.auth(token)

    nutrition = await get_nutrition(food_name, grams)  # now properly awaited

    data = supabase.table("food_entries").insert({
        "user_id":   user_id,
        "food_name": food_name,
        "grams":     grams,
        "calories":  nutrition.get("calories", 0),
        "protein":   nutrition.get("protein",  0),
        "carbs":     nutrition.get("carbs",    0),
        "fats":      nutrition.get("fats",     0),
    }).execute()

    return {
        "message": "Food entry added to database",
        "data": data.data,
    }


def get_foods(user_id: str, token: str | None = None):
    if token:
        supabase.postgrest.auth(token)

    data = supabase.table("food_entries").select("*").eq("user_id", user_id).execute()
    return data.data


def get_today_foods(user_id: str):
    today_start, today_end = _today_range()
    data = (
        supabase.table("food_entries")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", today_start)
        .lte("created_at", today_end)
        .order("created_at", desc=True)
        .execute()
    )
    return data.data or []


def get_today_diet_entry(user_id: str):
    today_start, today_end = _today_range()
    data = (
        supabase.table("diet_entries")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", today_start)
        .lte("created_at", today_end)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return data.data[0] if data.data else None


def get_user_profile(user_id: str, token: str | None = None):
    for column in ("user_id", "id"):
        try:
            data = supabase.table("users").select("*").eq(column, user_id).limit(1).execute()
            if data.data:
                return data.data[0]
        except Exception:
            continue

    auth_user = get_supabase_auth_user(token) if token else {"metadata": {}}
    metadata = auth_user.get("metadata") or {}
    return {
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
    }


async def recommend_foods(user_id: str, token: str | None = None):
    if token:
        supabase.postgrest.auth(token)

    profile = get_user_profile(user_id, token=token)
    diet = _normalize_diet(profile.get("diet") or "Vegetarian")
    today_foods = get_today_foods(user_id)
    today_diet = get_today_diet_entry(user_id) or {}
    meals = {
        "breakfast": today_diet.get("breakfast"),
        "lunch": today_diet.get("lunch"),
        "dinner": today_diet.get("dinner"),
        "snacks": today_diet.get("snacks"),
    }
    totals = _totals(today_foods)
    context = {
        "profile": profile,
        "diet": diet,
        "today_foods": today_foods,
        "today_meals": meals,
        "totals": totals,
    }

    try:
        recommendations = _enforce_diet(await get_food_recommendations(context), context)
        source = "ai"
        warning = None
    except Exception as exc:
        logger.exception("AI food recommendations failed for user_id=%s", user_id)
        recommendations = _contextual_fallback(context)
        source = "local_fallback"
        warning = "Using local recommendations because AI recommendations are temporarily unavailable."

    return {
        "message": "Recommendations generated successfully",
        "diet": diet,
        "recommendation_source": source,
        "warning": warning,
        "based_on": {
            "meals": meals,
            "totals": totals,
            "foods_logged": len(today_foods),
        },
        "data": recommendations,
    }
