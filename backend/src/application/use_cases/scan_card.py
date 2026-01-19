# FILE: src/application/use_cases/scan_card.py
from typing import List, Optional, Dict, Any
import logging
import time
import numpy as np
import cv2
from pathlib import Path

from domain.entities import ScanResult
from domain.entities.scan_result import BoundingBox
from domain.errors import CardNotDetectedError
from domain.value_objects import CardROIs
from interfaces.vision import ICardDetector, IROIExtractor, ISetSymbolClassifier
from interfaces.ocr import IOCRService, OCRResult

logger = logging.getLogger(__name__)

DEBUG_FRAMES_DIR = Path(__file__).parent.parent.parent.parent / "debug_frames"
DEBUG_FRAMES_DIR.mkdir(exist_ok=True)


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

    def execute(self, image: np.ndarray, debug_info: Optional[Dict[str, Any]] = None) -> ScanResult:
        ts = int(time.time() * 1000)
        h, w = image.shape[:2]
        logger.info(f"[SCAN] Frame: {w}x{h}")
        
        # Always build ROI boxes in original frame coords (for overlay even if detection fails)
        roi_boxes = self._build_roi_boxes_on_frame(w, h)
        
        card_contour = self._detector.find_card_contour(image)
        if card_contour is None:
            logger.warning("[SCAN] No card contour")
            # Return with ROI boxes so frontend shows something
            return ScanResult(
                name="", number="", set="unknown", language="unknown", 
                confidence=0.0, boxes=tuple(roi_boxes)
            )

        logger.info("[SCAN] Card found, warping...")
        warped = self._detector.warp_from_contour(image, card_contour)
        wh, ww = warped.shape[:2]
        
        rois = self._roi_extractor.extract(warped)

        # Preprocess ROIs for better OCR
        title_roi = self._preprocess_roi(rois["title"])
        number_roi = self._preprocess_roi(rois["number"])

        # Save ROI debug images
        if debug_info is not None:
            title_path = str(DEBUG_FRAMES_DIR / f"title_roi_{ts}.jpg")
            number_path = str(DEBUG_FRAMES_DIR / f"bottom_left_roi_{ts}.jpg")
            cv2.imwrite(title_path, title_roi)
            cv2.imwrite(number_path, number_roi)
            debug_info["saved_title_roi_path"] = f"/static/debug_frames/title_roi_{ts}.jpg"
            debug_info["saved_bottom_left_roi_path"] = f"/static/debug_frames/bottom_left_roi_{ts}.jpg"
            logger.info(f"[SCAN] Saved ROIs: {title_path}, {number_path}")

        logger.info("[SCAN] OCR on title...")
        title_results = self._ocr.read(title_roi)
        raw_title = " ".join([r.text for r in title_results])
        logger.info(f"[SCAN] Title OCR: {raw_title}")
        
        logger.info("[SCAN] OCR on number...")
        number_results = self._ocr.read(number_roi)
        raw_number = " ".join([r.text for r in number_results])
        logger.info(f"[SCAN] Number OCR: {raw_number}")

        if debug_info is not None:
            debug_info["raw_ocr_title"] = raw_title
            debug_info["raw_ocr_bottom_left"] = raw_number

        # Language detection
        full_ocr = self._ocr.read(warped)
        language = self._detect_language(full_ocr)

        # Set classification
        set_code, set_conf = ("unknown", 0.0)
        if self._set_classifier:
            set_code, set_conf = self._set_classifier.classify(rois["set_symbol"])

        # Parse results
        name = self._extract_best(title_results)
        number = self._extract_number(number_results)
        collection = self._extract_collection(number_results)
        confidence = self._calc_confidence(title_results, number_results, set_conf)

        # Build boxes in ORIGINAL frame coordinates
        boxes = self._build_boxes_from_contour(card_contour, w, h, name, confidence)
        boxes.extend(roi_boxes)
        
        logger.info(f"[SCAN] Result: name={name}, number={number}, collection={collection}, conf={confidence:.2f}, boxes={len(boxes)}")

        if self._debug:
            self._save_debug_image(warped, rois, title_results, number_results)

        return ScanResult(
            name=name, 
            number=number, 
            set=collection or set_code, 
            language=language, 
            confidence=confidence, 
            boxes=tuple(boxes)
        )

    def _preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        """Preprocess ROI for better OCR."""
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi
        
        # Bilateral filter (edge-preserving smoothing)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # CLAHE for contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh

    def _build_roi_boxes_on_frame(self, w: int, h: int) -> List[BoundingBox]:
        """Build ROI indicator boxes in original frame coordinates."""
        # Approximate ROI positions on original frame (assuming card fills ~80% of frame)
        card_x, card_y = int(w * 0.1), int(h * 0.05)
        card_w, card_h = int(w * 0.8), int(h * 0.9)
        
        rois = CardROIs()
        boxes = []
        
        # Title ROI
        tx = card_x + int(card_w * rois.title.x_start)
        ty = card_y + int(card_h * rois.title.y_start)
        tw = int(card_w * (rois.title.x_end - rois.title.x_start))
        th = int(card_h * (rois.title.y_end - rois.title.y_start))
        boxes.append(BoundingBox(label="roi_title", x=tx, y=ty, w=tw, h=th, conf=1.0))
        
        # Number/bottom-left ROI
        nx = card_x + int(card_w * rois.number.x_start)
        ny = card_y + int(card_h * rois.number.y_start)
        nw = int(card_w * (rois.number.x_end - rois.number.x_start))
        nh = int(card_h * (rois.number.y_end - rois.number.y_start))
        boxes.append(BoundingBox(label="roi_bottom_left", x=nx, y=ny, w=nw, h=nh, conf=1.0))
        
        return boxes

    def _build_boxes_from_contour(self, contour: np.ndarray, w: int, h: int, name: str, conf: float) -> List[BoundingBox]:
        """Build card bounding box in original frame coordinates."""
        boxes = []
        if contour is not None:
            x, y, bw, bh = cv2.boundingRect(contour)
            label = name if name else "card"
            boxes.append(BoundingBox(label=label, x=int(x), y=int(y), w=int(bw), h=int(bh), conf=float(conf)))
        return boxes

    def _detect_language(self, ocr_results: List[OCRResult]) -> str:
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
        """Extract card number like 001/131."""
        import re
        for r in results:
            match = re.search(r'\d{1,3}\s*/\s*\d{1,3}', r.text)
            if match:
                return match.group().replace(' ', '')
        return ""

    def _extract_collection(self, results: List[OCRResult]) -> str:
        """Extract collection code like PRE, SV8, etc."""
        import re
        for r in results:
            # Look for 2-4 letter codes
            match = re.search(r'\b([A-Z]{2,4})\b', r.text.upper())
            if match:
                code = match.group(1)
                if code not in ['THE', 'AND', 'FOR']:  # Skip common words
                    return code
        return ""

    def _calc_confidence(self, title: List[OCRResult], number: List[OCRResult], set_conf: float = 0.0) -> float:
        all_confs = [r.confidence for r in title + number]
        if set_conf > 0:
            all_confs.append(set_conf)
        return sum(all_confs) / len(all_confs) if all_confs else 0.0

    def _save_debug_image(self, warped: np.ndarray, rois: dict, title_results: List[OCRResult], number_results: List[OCRResult]):
        debug_img = warped.copy()
        h, w = warped.shape[:2]
        card_rois = CardROIs()
        
        for name, roi in [("title", card_rois.title), ("number", card_rois.number), ("set_symbol", card_rois.set_symbol)]:
            x1, y1, x2, y2 = roi.to_absolute(w, h)
            color = (0, 255, 0) if name == "title" else (255, 255, 0) if name == "number" else (255, 0, 255)
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(debug_img, name, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
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
