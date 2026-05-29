from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DietEntryCreate(BaseModel):
    user_id: Optional[str] = None
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    dinner: Optional[str] = None
    snacks: Optional[str] = None


class DietEntryUpdate(BaseModel):
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    dinner: Optional[str] = None
    snacks: Optional[str] = None


class DietEntryResponse(BaseModel):
    id: str
    user_id: str
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    dinner: Optional[str] = None
    snacks: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class AIRecommendationRequest(BaseModel):
    breakfast: Optional[str] = None
    lunch: Optional[str] = None
    dinner: Optional[str] = None
    snacks: Optional[str] = None


class AIRecommendationResponse(BaseModel):
    recommendation: str
    based_on: dict
