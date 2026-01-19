# FILE: src/api/dependencies.py
from infrastructure.ocr import EasyOCRService

_ocr_service = None


def get_ocr_service():
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = EasyOCRService(languages=["en"], gpu=False)
    return _ocr_service
