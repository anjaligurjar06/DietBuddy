from fastapi import APIRouter, Header, HTTPException
from app.models.user_model import UserCreate, UserProfile
from app.services.auth_service import create_user, get_profile, login_user, save_profile
from pydantic import BaseModel


class UserLogin(BaseModel):
    email: str
    password: str

router = APIRouter()

# handle user signup
@router.post("/signup")
def signup(user: UserCreate):
    return create_user(user)

# handle user login
@router.post("/login")
def login(user: UserLogin):
    return login_user(user.email, user.password)

# handle profile creation/update
@router.post("/profile")
def profile(user: UserProfile, authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    result = save_profile(user, authorization.removeprefix("Bearer ").strip())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# handle profile retrieval
@router.get("/profile/{user_id}")
def profile_by_user(user_id: str, authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ").strip() if authorization.startswith("Bearer ") else None
    result = get_profile(user_id, token=token)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
