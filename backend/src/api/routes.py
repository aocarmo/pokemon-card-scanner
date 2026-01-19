# FILE: src/api/routes.py
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import cv2
import numpy as np
import csv
import os
from pathlib import Path

from api.dependencies import get_scanner

router = APIRouter()

STATIC_DIR = Path(__file__).parent.parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

CSV_PATH = Path(__file__).parent.parent.parent / "data" / "inventory.csv"
CSV_PATH.parent.mkdir(exist_ok=True)


class ConfirmCardRequest(BaseModel):
    name: str
    collection: str
    number: str
    language: str


@router.post("/scan")
async def scan_card(file: UploadFile = File(...), debug: bool = Query(False)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    debug_path = str(STATIC_DIR / "debug_output.jpg") if debug else None
    scanner = get_scanner(debug=debug, debug_output_path=debug_path)

    try:
        result = scanner.execute(image)
        response = result.to_dict()
        if debug and debug_path and os.path.exists(debug_path):
            response["debug_image"] = "/static/debug_output.jpg"
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(status_code=422, content={"error": str(e), "name": "", "number": "", "set": "", "language": "", "confidence": 0.0, "boxes": []})


@router.post("/cards/confirm")
async def confirm_card(request: ConfirmCardRequest):
    rows = []
    found = False

    if CSV_PATH.exists():
        with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['name'] == request.name and row['collection'] == request.collection and row['number'] == request.number and row['language'] == request.language:
                    row['quantity'] = str(int(row['quantity']) + 1)
                    found = True
                rows.append(row)

    if not found:
        rows.append({'name': request.name, 'collection': request.collection, 'number': request.number, 'language': request.language, 'quantity': '1'})

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
