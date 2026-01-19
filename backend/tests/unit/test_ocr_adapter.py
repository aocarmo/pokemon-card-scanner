# FILE: tests/unit/test_ocr_adapter.py
import numpy as np
import pytest
from typing import List

from interfaces.ocr import IOCRService, OCRResult


class MockOCRService(IOCRService):
    """Mock OCR for testing - returns predefined results."""
    def __init__(self, results: List[OCRResult] = None):
        self._results = results or []

    def read(self, image: np.ndarray) -> List[OCRResult]:
        return self._results


class TestOCRServiceContract:
    def test_implements_interface(self):
        service = MockOCRService()
        assert isinstance(service, IOCRService)

    def test_read_returns_list_of_ocr_results(self):
        expected = [OCRResult(text="Pikachu", confidence=0.95, bbox=(0, 0, 100, 50))]
        service = MockOCRService(results=expected)
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = service.read(img)
        assert result == expected

    def test_read_returns_empty_list_when_no_text(self):
        service = MockOCRService(results=[])
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = service.read(img)
        assert result == []

    def test_ocr_result_fields(self):
        result = OCRResult(text="Test", confidence=0.8, bbox=(10, 20, 30, 40))
        assert result.text == "Test"
        assert result.confidence == 0.8
        assert result.bbox == (10, 20, 30, 40)

    def test_ocr_result_bbox_optional(self):
        result = OCRResult(text="Test", confidence=0.8)
        assert result.bbox is None
