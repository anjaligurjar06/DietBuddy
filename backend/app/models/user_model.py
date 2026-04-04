from pydantic import BaseModel
class UserCreate(BaseModel):
    name:str
    age:int
    gender:str
    height: float
    weight: float
    goal:str
    health:str 
    allergies:str
    diet:str
    activity:str
    email:str
    password:str
