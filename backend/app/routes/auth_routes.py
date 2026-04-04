from fastapi import APIRouter
from app.models.user_model import UserCreate
from app.services.auth_service import create_user, login_user
from pydantic import BaseModel
class UserLogin(BaseModel):
    email: str
    password: str
router= APIRouter()
@router.post("/signup")
def signup(user: UserCreate):
    return create_user(user)

@router.post("/login")
def login(user: UserLogin):
    return login_user(user.email, user.password)