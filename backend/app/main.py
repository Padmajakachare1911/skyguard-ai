from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.violations import router as violations_router
from app.routers.telemetry import router as telemetry_router
from app.database import engine, Base
from app import models


app = FastAPI()

# Allow React frontend to communicate with FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(violations_router)
app.include_router(telemetry_router)


@app.get("/")
def home():
    return {
        "message": "Welcome Rachna!",
        "project": "SkyGuard AI",
        "version": "1.0"
    }