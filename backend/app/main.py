import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure 'backend' directory is in sys.path so 'app' is always importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.routers.violations import router as violations_router
from app.routers.telemetry import router as telemetry_router
from app.routers.detect import router as detect_router
from app.database import engine, Base
from app import models


app = FastAPI()

# Allow React frontend to communicate from localhost, LAN IPs, or tunnel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

Base.metadata.create_all(bind=engine)

app.include_router(violations_router)
app.include_router(telemetry_router)
app.include_router(detect_router)


@app.get("/")
def home():
    return {
        "message": "Welcome Rachna!",
        "project": "SkyGuard AI",
        "version": "1.0"
    }