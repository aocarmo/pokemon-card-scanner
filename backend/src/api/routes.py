# FILE: src/api/routes.py
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import cv2
import numpy as np
import csv
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

DETECTION_THRESHOLD = 0.4


class ConfirmCardRequest(BaseModel):
    name: str
    collection: str
    number: str
    language: str


@router.post("/scan")
async def scan_card(file: UploadFile = File(...), debug: bool = Query(False)):
    ts = int(time.time() * 1000)
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    h, w = image.shape[:2]
    
    # Fix rotation if needed
    if w > h:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        h, w = image.shape[:2]

    if debug:
        cv2.imwrite(str(DEBUG_FRAMES_DIR / f"frame_{ts}.jpg"), image)

    scanner = get_scanner(debug=debug, debug_output_path=str(STATIC_DIR / "debug.jpg"))
    
    # Phase 1: Detection only
    contour, detection_conf = scanner.detect_card(image)
    
    if contour is None:
        return JSONResponse(content={
            "detected": False,
            "detection_confidence": 0.0,
            "card_quad": None,
            "result": None
        })
    
    # Convert contour to quad points
    quad = contour.reshape(4, 2).tolist()
    
    if detection_conf < DETECTION_THRESHOLD:
        return JSONResponse(content={
            "detected": True,
            "detection_confidence": detection_conf,
            "card_quad": quad,
            "result": None
        })
    
    # Phase 2: Full processing
    logger.info(f"[API] Detection confident ({detection_conf:.2f}), running OCR...")
    
    try:
        result = scanner.process_card(image, contour)
        
        if debug:
            warped = scanner.get_warped(image, contour)
            if warped is not None:
                cv2.imwrite(str(DEBUG_FRAMES_DIR / f"warped_{ts}.jpg"), warped)
        
        return JSONResponse(content={
            "detected": True,
            "detection_confidence": detection_conf,
            "card_quad": quad,
            "result": {
                "name": result.get("name") or None,
                "number": result.get("number") or None,
                "collection": result.get("collection") or None,
                "language": result.get("language"),
                "confidence": result.get("confidence", 0.0)
            }
        })
    except Exception as e:
        logger.warning(f"[API] OCR failed: {e}")
        return JSONResponse(content={
            "detected": True,
            "detection_confidence": detection_conf,
            "card_quad": quad,
            "result": None
        })


@router.post("/cards/confirm")
async def confirm_card(request: ConfirmCardRequest):
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

    return {"status": "ok"}


@router.get("/cards")
async def list_cards():
    if not CSV_PATH.exists():
        return {"cards": []}
    with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
        return {"cards": list(csv.DictReader(f))}
