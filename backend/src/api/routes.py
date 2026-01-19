# FILE: src/api/routes.py
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import cv2
import numpy as np
import csv
import logging
from pathlib import Path

from api.dependencies import get_ocr_service
from application.use_cases.scan_card import ScanCardUseCase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()

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
        raise HTTPException(status_code=400, detail="Invalid image")

    logger.info(f"[API] /scan debug={debug}, shape={image.shape}")

    scanner = ScanCardUseCase(ocr_service=get_ocr_service(), debug=debug)
    result = scanner.scan(image)
    
    logger.info(f"[API] Result: status={result['status']}, name={result['name']}, boxes={len(result['boxes'])}")
    
    return JSONResponse(content=result)


@router.post("/cards/confirm")
async def confirm_card(request: ConfirmCardRequest):
    rows = []
    found = False

    if CSV_PATH.exists():
        with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
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
