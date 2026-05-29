from fastapi import APIRouter, Header, HTTPException
from app.services.auth_service import get_supabase_auth_user
from app.services.food_service import add_food, get_foods, recommend_foods
from app.models.food_model import FoodCreate, FoodRecommendationResponse, FoodResponse
from uuid import UUID

router = APIRouter()

# Helper function to extract and validate token, and ensure the user is accessing their own data
def _get_token_user(authorization: str, expected_user_id: str):
    if not authorization.startswith("Bearer "):
        return None, None

    token = authorization.removeprefix("Bearer ").strip()
    auth_user = get_supabase_auth_user(token)
    if auth_user.get("id") != expected_user_id:
        raise HTTPException(status_code=403, detail="Cannot access another user's food data")
    return token, auth_user

# POST /food/add
@router.post("/add", response_model=FoodResponse)
async def create_food(payload: FoodCreate, authorization: str = Header(default="")):  
    token, _ = _get_token_user(authorization, str(payload.user_id))
    return await add_food(
        user_id=str(payload.user_id),
        food_name=payload.food_name,
        grams=payload.grams,
        token=token,
    )

# GET /food/recommendations/{user_id}
@router.get("/recommendations/{user_id}", response_model=FoodRecommendationResponse)
async def fetch_recommendations(user_id: UUID, authorization: str = Header(default="")):
    token = None
    if authorization.startswith("Bearer "):
        token, _ = _get_token_user(authorization, str(user_id))

    return await recommend_foods(str(user_id), token=token)

# GET /food/{user_id}
@router.get("/{user_id}", response_model=FoodResponse)
async def fetch_foods(user_id: UUID, authorization: str = Header(default="")):
    token, _ = _get_token_user(authorization, str(user_id))
    foods = get_foods(str(user_id), token=token)
    return {
        "message": "Foods retrieved successfully",
        "data": foods,
    }
    
