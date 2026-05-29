from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, diet_routes, food_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Diet and Food API!"}

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(food_routes.router, prefix="/food", tags=["food"])
app.include_router(diet_routes.router, prefix="/diet", tags=["diet"])
