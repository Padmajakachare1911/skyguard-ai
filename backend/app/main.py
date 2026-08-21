from fastapi import FastAPI
from app.routers.violations import router as violations_router
from app.database import engine, Base
from app import models


app = FastAPI()
Base.metadata.create_all(bind=engine)
app.include_router(violations_router)

@app.get("/")
def home():
    return {
    "message": "Welcome Rachna!",
    "project": "SkyGuard AI",
    "version": "1.0"}
