# FILE: src/api/app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import router

app = FastAPI(title="Pokemon Card Scanner API", version="1.0.0")

STATIC_DIR = Path(__file__).parent.parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
