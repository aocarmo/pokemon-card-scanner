# FILE: src/application/use_cases/scan_card.py
from typing import List, Optional, Tuple, Dict, Any
import logging
import re
import numpy as np
import cv2

from domain.value_objects import CardROIs
from interfaces.vision import ICardDetector, IROIExtractor, ISetSymbolClassifier
from interfaces.ocr import IOCRService, OCRResult

logger = logging.getLogger(__name__)


class ScanCardUseCase:
    ENGLISH_KEYWORDS = ["BASIC", "STAGE", "TRAINER", "ENERGY", "ITEM", "SUPPORTER", "WEAKNESS", "RESISTANCE", "RETREAT"]
    PORTUGUESE_KEYWORDS = ["BÁSICO", "ESTÁGIO", "TREINADOR", "ENERGIA", "APOIADOR", "FRAQUEZA", "RESISTÊNCIA", "RECUAR"]

    def __init__(
        self,
        detector: ICardDetector,
        roi_extractor: IROIExtractor,
        ocr_service: IOCRService,
        set_classifier: ISetSymbolClassifier = None,
        debug: bool = False,
        debug_output_path: str = "debug_output.jpg"
    ):
        self._detector = detector
        self._roi_extractor = roi_extractor
        self._ocr = ocr_service
        self._set_classifier = set_classifier
        self._debug = debug
        self._debug_path = debug_output_path

    def detect_card(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], float]:
        """Phase 1: Fast detection only. Returns (contour, confidence)."""
        contour = self._detector.find_card_contour(image)
        if contour is None:
            return None, 0.0
        
        # Compute detection confidence based on contour quality
        conf = self._compute_detection_confidence(contour, image.shape)
        return contour, conf

    def _compute_detection_confidence(self, contour: np.ndarray, img_shape: tuple) -> float:
        """Estimate detection confidence from contour properties."""
        h, w = img_shape[:2]
        img_area = h * w
        
        # Contour area ratio
        contour_area = cv2.contourArea(contour)
        area_ratio = contour_area / img_area
        
        # Card should be 10-90% of frame
        if area_ratio < 0.05 or area_ratio > 0.95:
            return 0.1
        
        # Check aspect ratio (Pokemon cards are ~2.5:3.5)
        rect = cv2.minAreaRect(contour)
        rw, rh = rect[1]
        if rw == 0 or rh == 0:
            return 0.1
        aspect = max(rw, rh) / min(rw, rh)
        # Expected ~1.4, allow 1.2-1.8
        aspect_score = 1.0 - min(abs(aspect - 1.4) / 0.4, 1.0)
        
        # Combine scores
        area_score = min(area_ratio / 0.3, 1.0) if area_ratio < 0.3 else 1.0
        conf = (area_score * 0.5 + aspect_score * 0.5)
        
        return round(conf, 2)

    def get_warped(self, image: np.ndarray, contour: np.ndarray) -> Optional[np.ndarray]:
        """Get warped card image."""
        return self._detector.warp_from_contour(image, contour)

    def process_card(self, image: np.ndarray, contour: np.ndarray) -> Dict[str, Any]:
        """Phase 2: Full OCR processing. Returns result dict."""
        warped = self._detector.warp_from_contour(image, contour)
        rois = self._roi_extractor.extract(warped)

        # Preprocess ROIs
        title_roi = self._preprocess_roi(rois["title"])
        number_roi = self._preprocess_roi(rois["number"])

        # OCR
        title_results = self._ocr.read(title_roi)
        number_results = self._ocr.read(number_roi)
        
        logger.info(f"[SCAN] Title OCR: {[r.text for r in title_results]}")
        logger.info(f"[SCAN] Number OCR: {[r.text for r in number_results]}")

        # Language detection
        full_ocr = self._ocr.read(warped)
        language = self._detect_language(full_ocr)

        # Extract fields
        name = self._extract_best(title_results)
        number = self._extract_number(number_results)
        collection = self._extract_collection(number_results)
        
        # Set classifier fallback
        if not collection and self._set_classifier:
            collection, _ = self._set_classifier.classify(rois["set_symbol"])
            if collection == "unknown":
                collection = None

        confidence = self._calc_confidence(title_results, number_results)

        if self._debug:
            self._save_debug_image(warped, rois, title_results, number_results)

        return {
            "name": name,
            "number": number,
            "collection": collection,
            "language": language,
            "confidence": confidence
        }

    def _preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        return enhanced

    def _detect_language(self, ocr_results: List[OCRResult]) -> Optional[str]:
        all_text = " ".join([r.text.upper() for r in ocr_results])
        en_count = sum(1 for kw in self.ENGLISH_KEYWORDS if kw in all_text)
        pt_count = sum(1 for kw in self.PORTUGUESE_KEYWORDS if kw in all_text)
        if pt_count > en_count:
            return "pt"
        elif en_count > 0:
            return "en"
        return None

    def _extract_best(self, results: List[OCRResult]) -> str:
        if not results:
            return ""
        best = max(results, key=lambda r: r.confidence)
        return best.text.strip() if best.confidence > 0.2 else ""

    def _extract_number(self, results: List[OCRResult]) -> str:
        for r in results:
            match = re.search(r'\d{1,3}\s*/\s*\d{1,3}', r.text)
            if match:
                return match.group().replace(' ', '')
        return ""

    def _extract_collection(self, results: List[OCRResult]) -> str:
        for r in results:
            match = re.search(r'\b([A-Z]{2,4})\b', r.text.upper())
            if match:
                code = match.group(1)
                if code not in ['THE', 'AND', 'FOR', 'HP']:
                    return code
        return ""

    def _calc_confidence(self, title: List[OCRResult], number: List[OCRResult]) -> float:
        all_confs = [r.confidence for r in title + number]
        return sum(all_confs) / len(all_confs) if all_confs else 0.0

    def _save_debug_image(self, warped: np.ndarray, rois: dict, title_results: List[OCRResult], number_results: List[OCRResult]):
        debug_img = warped.copy()
        h, w = warped.shape[:2]
        card_rois = CardROIs()
        for name, roi in [("title", card_rois.title), ("number", card_rois.number)]:
            x1, y1, x2, y2 = roi.to_absolute(w, h)
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.imwrite(self._debug_path, debug_img)
