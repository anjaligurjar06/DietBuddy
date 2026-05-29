from fastapi import APIRouter, Depends, Header, HTTPException, status
from supabase import Client

from app.core.supabase import get_supabase
from app.services.auth_service import get_supabase_auth_user
from app.models.diet_model import (
    DietEntryCreate,
    DietEntryUpdate,
    DietEntryResponse,
    AIRecommendationRequest,
    AIRecommendationResponse,
)
from app.services.diet_service import (
    create_diet_entry,
    get_entries_by_user,
    get_today_entry,
    get_all_entries,
    update_diet_entry,
    delete_diet_entry,
    get_ai_recommendation,
)
from app.utils.auth_utils import get_current_user   
router = APIRouter()


@router.post("/add", response_model=DietEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_diet_entry(
    data: DietEntryCreate,
    authorization: str = Header(default=""),
    supabase: Client = Depends(get_supabase),
):
    """Compatibility endpoint used by the current React diet form."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    auth_user = get_supabase_auth_user(token)
    user_id = auth_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    try:
        return create_diet_entry(supabase, user_id, data, token=token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── POST /diet/entry ─────────────────────────────────────────────────────────
@router.post("/entry", response_model=DietEntryResponse, status_code=status.HTTP_201_CREATED)
async def log_diet_entry(
    data: DietEntryCreate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """Log a new diet entry (breakfast / lunch / dinner / snacks) for today."""
    try:
        entry = create_diet_entry(supabase, current_user["id"], data)
        return entry
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── GET /diet/today ──────────────────────────────────────────────────────────
@router.get("/today", response_model=DietEntryResponse)
async def get_today_diet(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """Get the current user's diet entry for today."""
    entry = get_today_entry(supabase, current_user["id"])
    if not entry:
        raise HTTPException(status_code=404, detail="No diet entry found for today")
    return entry


# GET diet/history
@router.get("/history", response_model=list[DietEntryResponse])
async def get_diet_history(
    limit: int = 30,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """Get the last N diet entries for the current user (default 30)."""
    entries = get_all_entries(supabase, current_user["id"], limit=limit)
    return entries


@router.get("/{user_id}")
async def get_user_diet_entries(
    user_id: str,
    supabase: Client = Depends(get_supabase),
):
    """Compatibility endpoint used by the current React login flow."""
    return {
        "message": "Diet entries retrieved successfully",
        "data": get_entries_by_user(supabase, user_id),
    }


# PUT /diet/entry/{entry_id}
@router.put("/entry/{entry_id}", response_model=DietEntryResponse)
async def update_entry(
    entry_id: str,
    data: DietEntryUpdate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """Update an existing diet entry (only fields provided will be changed)."""
    try:
        entry = update_diet_entry(supabase, entry_id, current_user["id"], data)
        return entry
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# DELETE /diet/entry/{entry_id}
@router.delete("/entry/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """Delete a diet entry."""
    deleted = delete_diet_entry(supabase, entry_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found or not authorised")


# POST /diet/recommend 
@router.post("/recommend", response_model=AIRecommendationResponse)
async def get_recommendation(
    body: AIRecommendationRequest = AIRecommendationRequest(),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """
    Get an AI-powered nutrition recommendation based on today's meals.
    If no override is provided in the request body, today's logged entry is used.
    """
    # Use override if provided, else fall back to today's DB entry
    if any([body.breakfast, body.lunch, body.dinner, body.snacks]):
        meals = body.model_dump()
    else:
        entry = get_today_entry(supabase, current_user["id"])
        if not entry:
            raise HTTPException(
                status_code=404,
                detail="No diet entry for today. Log your meals first or provide them in the request body.",
            )
        meals = {
            "breakfast": entry.get("breakfast"),
            "lunch":     entry.get("lunch"),
            "dinner":    entry.get("dinner"),
            "snacks":    entry.get("snacks"),
        }

    try:
        recommendation = await get_ai_recommendation(meals)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")

    return AIRecommendationResponse(recommendation=recommendation, based_on=meals)
