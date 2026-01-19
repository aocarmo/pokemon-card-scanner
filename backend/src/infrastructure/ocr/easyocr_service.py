# FILE: src/infrastructure/ocr/easyocr_service.py
from typing import List
import numpy as np
import cv2
import easyocr

from interfaces.ocr import IOCRService, OCRResult


class EasyOCRService(IOCRService):
    def __init__(self, languages: List[str] = None, gpu: bool = False):
        self._reader = easyocr.Reader(languages or ["en"], gpu=gpu)

    def read(self, image: np.ndarray) -> List[OCRResult]:
        preprocessed = self._preprocess(image)
        results = self._reader.readtext(preprocessed)
        return [
            OCRResult(
                text=text,
                confidence=float(conf),
                bbox=self._bbox_to_tuple(bbox)
            )
            for bbox, text, conf in results
        ]

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        return enhanced

    def _bbox_to_tuple(self, bbox) -> tuple:
        pts = np.array(bbox)
        x_min, y_min = pts.min(axis=0).astype(int)
        x_max, y_max = pts.max(axis=0).astype(int)
        return (int(x_min), int(y_min), int(x_max), int(y_max))
