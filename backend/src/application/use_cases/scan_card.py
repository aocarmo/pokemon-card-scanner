# FILE: src/application/use_cases/scan_card.py
from typing import List, Optional
import numpy as np
import cv2

from domain.entities import ScanResult
from domain.errors import CardNotDetectedError
from interfaces.vision import ICardDetector, IROIExtractor, ISetSymbolClassifier
from interfaces.ocr import IOCRService, OCRResult


class ScanCardUseCase:
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

    def execute(self, image: np.ndarray) -> ScanResult:
        warped = self._detector.detect_and_warp(image)
        if warped is None:
            raise CardNotDetectedError("No card detected in image")

        rois = self._roi_extractor.extract(warped)
        title_results = self._ocr.read(rois["title"])
        number_results = self._ocr.read(rois["number"])

        set_code, set_conf = ("unknown", 0.0)
        if self._set_classifier:
            set_code, set_conf = self._set_classifier.classify(rois["set_symbol"])

        if self._debug:
            self._save_debug_image(warped, rois, title_results, number_results)

        name = self._extract_best(title_results)
        number = self._extract_best(number_results)
        confidence = self._calc_confidence(title_results, number_results, set_conf)

        return ScanResult(name=name, number=number, set=set_code, confidence=confidence)

    def _extract_best(self, results: List[OCRResult]) -> str:
        if not results:
            return ""
        best = max(results, key=lambda r: r.confidence)
        return best.text.strip() if best.confidence > 0.3 else ""

    def _calc_confidence(self, title: List[OCRResult], number: List[OCRResult], set_conf: float = 0.0) -> float:
        all_confs = [r.confidence for r in title + number]
        if set_conf > 0:
            all_confs.append(set_conf)
        if not all_confs:
            return 0.0
        return sum(all_confs) / len(all_confs)

    def _save_debug_image(
        self,
        warped: np.ndarray,
        rois: dict,
        title_results: List[OCRResult],
        number_results: List[OCRResult]
    ):
        debug_img = warped.copy()
        h, w = warped.shape[:2]

        # Draw ROI rectangles
        from domain.value_objects import CardROIs
        card_rois = CardROIs()
        for name, roi in [("title", card_rois.title), ("number", card_rois.number), ("set_symbol", card_rois.set_symbol)]:
            x1, y1, x2, y2 = roi.to_absolute(w, h)
            color = (0, 255, 0) if name != "set_symbol" else (255, 255, 0)
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(debug_img, name, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Draw OCR bboxes within ROIs
        self._draw_ocr_boxes(debug_img, title_results, card_rois.title.to_absolute(w, h))
        self._draw_ocr_boxes(debug_img, number_results, card_rois.number.to_absolute(w, h))

        cv2.imwrite(self._debug_path, debug_img)

    def _draw_ocr_boxes(self, img: np.ndarray, results: List[OCRResult], roi_offset: tuple):
        rx, ry, _, _ = roi_offset
        for r in results:
            if r.bbox:
                x1, y1, x2, y2 = r.bbox
                cv2.rectangle(img, (rx + x1, ry + y1), (rx + x2, ry + y2), (0, 0, 255), 1)
                cv2.putText(img, f"{r.text} ({r.confidence:.2f})", (rx + x1, ry + y1 - 3),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
