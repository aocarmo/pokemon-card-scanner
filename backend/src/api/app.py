# FILE: src/api/app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pokemon Card Scanner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent.parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

DEBUG_FRAMES_DIR = Path(__file__).parent.parent.parent / "debug_frames"
DEBUG_FRAMES_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static/debug_frames", StaticFiles(directory=str(DEBUG_FRAMES_DIR)), name="debug_frames")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    logger.info("[API] Pokemon Card Scanner API started")
    logger.info(f"[API] Static: {STATIC_DIR}")
    logger.info(f"[API] Debug frames: {DEBUG_FRAMES_DIR}")
