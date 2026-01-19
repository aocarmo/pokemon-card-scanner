# FILE: src/api/routes.py
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import tempfile
import os
from pathlib import Path

from api.dependencies import get_scanner

router = APIRouter()

STATIC_DIR = Path(__file__).parent.parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


@router.post("/scan")
async def scan_card(
    file: UploadFile = File(...),
    debug: bool = Query(False)
):
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
        return JSONResponse(
            status_code=422,
            content={"error": str(e), "name": "", "number": "", "confidence": 0.0}
        )
