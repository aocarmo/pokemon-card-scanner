# FILE: src/api/routes.py
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import cv2
import numpy as np
import csv
import os
import logging
import time
from pathlib import Path

from api.dependencies import get_scanner

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()

STATIC_DIR = Path(__file__).parent.parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

DEBUG_FRAMES_DIR = Path(__file__).parent.parent.parent / "debug_frames"
DEBUG_FRAMES_DIR.mkdir(exist_ok=True)

CSV_PATH = Path(__file__).parent.parent.parent / "data" / "inventory.csv"
CSV_PATH.parent.mkdir(exist_ok=True)


class ConfirmCardRequest(BaseModel):
    name: str
    collection: str
    number: str
    language: str


def fix_rotation(image: np.ndarray) -> tuple:
    """Fix sideways images (landscape when should be portrait)."""
    h, w = image.shape[:2]
    rotated = False
    # Pokemon cards are portrait - if width > height, rotate
    if w > h:
        logger.info(f"[API] Rotating image: {w}x{h} -> {h}x{w}")
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        rotated = True
    return image, rotated


@router.post("/scan")
async def scan_card(file: UploadFile = File(...), debug: bool = Query(False)):
    ts = int(time.time() * 1000)
    logger.info(f"[API] /scan file={file.filename}, debug={debug}")
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        logger.error("[API] Invalid image")
        raise HTTPException(status_code=400, detail="Invalid image file")

    orig_shape = image.shape
    logger.info(f"[API] Image: {orig_shape}")
    
    # Fix rotation
    image, rotation_applied = fix_rotation(image)
    if rotation_applied:
        logger.info(f"[API] After rotation: {image.shape}")

    debug_info = {
        "saved_frame_path": None,
        "saved_title_roi_path": None,
        "saved_bottom_left_roi_path": None,
        "raw_ocr_title": None,
        "raw_ocr_bottom_left": None,
        "rotation_applied": rotation_applied,
        "original_shape": list(orig_shape),
        "processed_shape": list(image.shape)
    }

    # Save debug frame
    if debug:
        frame_path = str(DEBUG_FRAMES_DIR / f"frame_{ts}.jpg")
        cv2.imwrite(frame_path, image)
        debug_info["saved_frame_path"] = f"/static/debug_frames/frame_{ts}.jpg"
        logger.info(f"[API] Saved frame: {frame_path}")

    debug_path = str(STATIC_DIR / "debug_output.jpg") if debug else None
    scanner = get_scanner(debug=debug, debug_output_path=debug_path)

    try:
        result = scanner.execute(image, debug_info=debug_info if debug else None)
        response = result.to_dict()
        
        if debug:
            response["debug"] = debug_info
            if debug_path and os.path.exists(debug_path):
                response["debug_image"] = "/static/debug_output.jpg"
        
        logger.info(f"[API] Success: name={response.get('name')}, boxes={len(response.get('boxes', []))}")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.warning(f"[API] Scan failed: {e}")
        # Return ROI boxes even on failure so overlay shows something
        h, w = image.shape[:2]
        fallback_boxes = [
            {"label": "roi_title", "x": int(w*0.05), "y": int(h*0.02), "w": int(w*0.8), "h": int(h*0.07), "conf": 0.0},
            {"label": "roi_bottom_left", "x": int(w*0.02), "y": int(h*0.90), "w": int(w*0.5), "h": int(h*0.08), "conf": 0.0}
        ]
        response = {
            "error": str(e), 
            "name": None, 
            "number": None, 
            "collection": None,
            "set": None, 
            "language": None, 
            "confidence": 0.0, 
            "boxes": fallback_boxes
        }
        if debug:
            response["debug"] = debug_info
        return JSONResponse(status_code=200, content=response)


@router.post("/cards/confirm")
async def confirm_card(request: ConfirmCardRequest):
    logger.info(f"[API] /cards/confirm: {request.name}")
    rows = []
    found = False

    if CSV_PATH.exists():
        with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row['name'] == request.name and 
                    row['collection'] == request.collection and 
                    row['number'] == request.number and 
                    row['language'] == request.language):
                    row['quantity'] = str(int(row['quantity']) + 1)
                    found = True
                rows.append(row)

    if not found:
        rows.append({
            'name': request.name, 
            'collection': request.collection, 
            'number': request.number, 
            'language': request.language, 
            'quantity': '1'
        })

    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'collection', 'number', 'language', 'quantity'])
        writer.writeheader()
        writer.writerows(rows)

    return {"status": "ok", "message": f"Card saved: {request.name}"}


@router.get("/cards")
async def list_cards():
    if not CSV_PATH.exists():
        return {"cards": []}
    with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
        return {"cards": list(csv.DictReader(f))}
