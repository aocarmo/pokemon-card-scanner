# FILE: tests/integration/test_scan_pipeline.py
"""
Integration test for the card scanning pipeline.

SETUP: Place a real Pokemon card image at tests/assets/sample_card.jpg
The image should show a single card on a contrasting background.
"""
import numpy as np
import pytest
from pathlib import Path
from typing import List

from domain.entities import ScanResult
from domain.errors import CardNotDetectedError
from interfaces.ocr import IOCRService, OCRResult
from infrastructure.vision import OpenCVCardDetector, OpenCVROIExtractor
from application.use_cases import ScanCardUseCase


ASSETS_DIR = Path(__file__).parent.parent / "assets"
SAMPLE_IMAGE = ASSETS_DIR / "sample_card.jpg"


class MockOCRService(IOCRService):
    """Mock OCR that returns realistic results for testing."""
    def read(self, image: np.ndarray) -> List[OCRResult]:
        return [OCRResult(text="Pikachu", confidence=0.92, bbox=(10, 10, 200, 50))]


@pytest.fixture
def scanner_with_mock_ocr():
    return ScanCardUseCase(
        detector=OpenCVCardDetector(),
        roi_extractor=OpenCVROIExtractor(),
        ocr_service=MockOCRService()
    )


@pytest.fixture
def synthetic_card_image():
    """Create synthetic card-like image for testing without real assets."""
    img = np.ones((600, 500, 3), dtype=np.uint8) * 200  # Gray background
    # Draw white rectangle (card)
    img[50:550, 75:425] = 255
    # Draw black border
    import cv2
    cv2.rectangle(img, (75, 50), (425, 550), (0, 0, 0), 3)
    return img


class TestScanPipeline:
    def test_scan_returns_result_with_required_fields(self, scanner_with_mock_ocr, synthetic_card_image):
        result = scanner_with_mock_ocr.execute(synthetic_card_image)
        assert isinstance(result, ScanResult)
        assert hasattr(result, "name")
        assert hasattr(result, "number")
        assert hasattr(result, "confidence")

    def test_scan_result_to_dict_has_all_keys(self, scanner_with_mock_ocr, synthetic_card_image):
        result = scanner_with_mock_ocr.execute(synthetic_card_image)
        d = result.to_dict()
        assert "name" in d
        assert "number" in d
        assert "confidence" in d

    def test_confidence_is_normalized(self, scanner_with_mock_ocr, synthetic_card_image):
        result = scanner_with_mock_ocr.execute(synthetic_card_image)
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.skipif(not SAMPLE_IMAGE.exists(), reason="Sample image not found")
    def test_with_real_image(self, scanner_with_mock_ocr):
        """Run with real image if available."""
        import cv2
        img = cv2.imread(str(SAMPLE_IMAGE))
        result = scanner_with_mock_ocr.execute(img)
        assert result.name or result.number  # At least one should be detected

    def test_raises_on_no_card_detected(self, scanner_with_mock_ocr):
        # Uniform image with no edges
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        with pytest.raises(CardNotDetectedError):
            scanner_with_mock_ocr.execute(img)
