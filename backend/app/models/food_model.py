from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class FoodCreate(BaseModel):
    user_id: UUID
    food_name: str
    grams: float


class FoodItem(BaseModel):
    id: UUID
    user_id: UUID
    food_name: str
    grams: float
    calories: float
    protein: float
    carbs: float
    fats: float
    created_at: Optional[datetime] = None


class FoodResponse(BaseModel):
    message: str
    data: List[FoodItem]


class FoodRecommendation(BaseModel):
    id: int
    food_name: str
    calories: float
    protein: float
    carbs: float
    fats: float
    reason: str


class FoodRecommendationResponse(BaseModel):
    message: str
    diet: str
    recommendation_source: Optional[str] = None
    warning: Optional[str] = None
    based_on: dict
    data: List[FoodRecommendation]
