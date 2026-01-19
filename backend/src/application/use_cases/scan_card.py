# FILE: src/application/use_cases/scan_card.py
from typing import List, Optional, Tuple, Dict, Any
import logging
import re
import time
import numpy as np
import cv2
from pathlib import Path

from domain.value_objects import CardROIs
from interfaces.ocr import IOCRService, OCRResult

logger = logging.getLogger(__name__)

DEBUG_DIR = Path(__file__).parent.parent.parent.parent / "debug_frames"
DEBUG_DIR.mkdir(exist_ok=True)

# Pokemon card aspect ratio is ~2.5" x 3.5" = 0.714 (w/h) or 1.4 (h/w)
CARD_ASPECT_MIN = 1.30
CARD_ASPECT_MAX = 1.50
CARD_AREA_MIN_RATIO = 0.08  # Card must be at least 8% of frame
WARP_WIDTH = 630
WARP_HEIGHT = 880


class ScanCardUseCase:
    ENGLISH_KW = ["BASIC", "STAGE", "TRAINER", "ENERGY", "WEAKNESS", "RESISTANCE", "RETREAT"]
    PORTUGUESE_KW = ["BÁSICO", "ESTÁGIO", "TREINADOR", "ENERGIA", "FRAQUEZA", "RESISTÊNCIA", "RECUAR"]

    def __init__(self, ocr_service: IOCRService, debug: bool = False):
        self._ocr = ocr_service
        self._debug = debug
        self._ts = int(time.time() * 1000)

    def scan(self, image: np.ndarray) -> Dict[str, Any]:
        h, w = image.shape[:2]
        logger.info(f"[SCAN] Frame: {w}x{h}")

        # Fix rotation if landscape
        rotated = False
        if w > h:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            h, w = image.shape[:2]
            rotated = True
            logger.info(f"[SCAN] Rotated to: {w}x{h}")

        debug_info = {"rotation_applied": rotated}

        if self._debug:
            p = str(DEBUG_DIR / f"frame_{self._ts}.jpg")
            cv2.imwrite(p, image)
            debug_info["saved_frame_path"] = p

        # Step 1: Detect card
        contour, conf = self._detect_card(image)
        
        if contour is None:
            return {
                "status": "no_card_detected",
                "name": None, "number": None, "collection": None,
                "language": None, "confidence": 0.0,
                "boxes": [],
                "debug": debug_info
            }

        # Card quad in original frame coords
        quad = contour.reshape(4, 2).tolist()
        boxes = [{"label": "card", "type": "quad", "points": quad, "conf": conf}]

        # Step 2: Warp card
        warped, M, M_inv = self._warp_card(image, contour)
        
        if self._debug:
            p = str(DEBUG_DIR / f"warp_{self._ts}.jpg")
            cv2.imwrite(p, warped)
            debug_info["saved_warp_path"] = p

        # Step 3: Extract ROIs from warped space
        rois = CardROIs()
        wh, ww = warped.shape[:2]
        
        title_coords = rois.title.to_absolute(ww, wh)
        bottom_coords = rois.number.to_absolute(ww, wh)
        
        title_roi = warped[title_coords[1]:title_coords[3], title_coords[0]:title_coords[2]]
        bottom_roi = warped[bottom_coords[1]:bottom_coords[3], bottom_coords[0]:bottom_coords[2]]

        # Preprocess ROIs
        title_proc = self._preprocess_roi(title_roi)
        bottom_proc = self._preprocess_roi(bottom_roi)

        if self._debug:
            cv2.imwrite(str(DEBUG_DIR / f"title_{self._ts}.jpg"), title_proc)
            cv2.imwrite(str(DEBUG_DIR / f"bottom_{self._ts}.jpg"), bottom_proc)
            debug_info["saved_title_roi_path"] = str(DEBUG_DIR / f"title_{self._ts}.jpg")
            debug_info["saved_bottom_left_roi_path"] = str(DEBUG_DIR / f"bottom_{self._ts}.jpg")

        # Step 4: OCR
        title_results = self._ocr.read(title_proc)
        bottom_results = self._ocr.read(bottom_proc)
        
        raw_title = " ".join([r.text for r in title_results])
        raw_bottom = " ".join([r.text for r in bottom_results])
        logger.info(f"[SCAN] OCR title: {raw_title}")
        logger.info(f"[SCAN] OCR bottom: {raw_bottom}")
        
        debug_info["raw_ocr_title"] = raw_title
        debug_info["raw_ocr_bottom_left"] = raw_bottom

        # Step 5: Extract fields
        name = self._extract_name(title_results)
        number = self._extract_number(bottom_results)
        collection = self._extract_collection(bottom_results)
        
        # Language from full card OCR
        full_results = self._ocr.read(warped)
        language = self._detect_language(full_results)

        # Step 6: Map ROI boxes back to original frame
        title_box_orig = self._map_roi_to_original(title_coords, M_inv, w, h)
        bottom_box_orig = self._map_roi_to_original(bottom_coords, M_inv, w, h)
        
        if title_box_orig:
            boxes.append({"label": "roi_title", **title_box_orig, "conf": 1.0})
        if bottom_box_orig:
            boxes.append({"label": "roi_bottom_left", **bottom_box_orig, "conf": 1.0})

        # Determine status
        ocr_conf = self._calc_confidence(title_results, bottom_results)
        status = "ok" if (name and number) else "ocr_failed"

        return {
            "status": status,
            "name": name or None,
            "number": number or None,
            "collection": collection or None,
            "language": language,
            "confidence": ocr_conf,
            "boxes": boxes,
            "debug": debug_info
        }

    def _detect_card(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], float]:
        """Detect card contour with strict validation."""
        h, w = image.shape[:2]
        frame_area = h * w

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 30, 100)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        best = None
        best_score = 0

        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            
            if len(approx) != 4:
                continue

            area = cv2.contourArea(approx)
            area_ratio = area / frame_area
            
            if area_ratio < CARD_AREA_MIN_RATIO:
                continue

            rect = cv2.minAreaRect(approx)
            rw, rh = rect[1]
            if rw == 0 or rh == 0:
                continue
            
            aspect = max(rw, rh) / min(rw, rh)
            
            if not (CARD_ASPECT_MIN <= aspect <= CARD_ASPECT_MAX):
                continue

            # Score based on area and aspect match
            aspect_score = 1.0 - abs(aspect - 1.4) / 0.2
            area_score = min(area_ratio / 0.3, 1.0)
            score = aspect_score * 0.6 + area_score * 0.4

            logger.info(f"[DETECT] Candidate: area={area_ratio:.2%}, aspect={aspect:.2f}, score={score:.2f}")

            if score > best_score:
                best_score = score
                best = approx

        if best is None:
            return None, 0.0

        return best, round(best_score, 2)

    def _warp_card(self, image: np.ndarray, contour: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Warp card to canonical size, return warped image and homography matrices."""
        pts = contour.reshape(4, 2).astype(np.float32)
        ordered = self._order_points(pts)
        
        dst = np.array([
            [0, 0],
            [WARP_WIDTH, 0],
            [WARP_WIDTH, WARP_HEIGHT],
            [0, WARP_HEIGHT]
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(ordered, dst)
        M_inv = cv2.getPerspectiveTransform(dst, ordered)
        warped = cv2.warpPerspective(image, M, (WARP_WIDTH, WARP_HEIGHT))
        
        return warped, M, M_inv

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Order: top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        d = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(d)]
        rect[3] = pts[np.argmax(d)]
        return rect

    def _map_roi_to_original(self, roi_coords: tuple, M_inv: np.ndarray, orig_w: int, orig_h: int) -> Optional[dict]:
        """Map ROI from warped space back to original frame."""
        x1, y1, x2, y2 = roi_coords
        corners = np.array([
            [[x1, y1]], [[x2, y1]], [[x2, y2]], [[x1, y2]]
        ], dtype=np.float32)
        
        transformed = cv2.perspectiveTransform(corners, M_inv)
        pts = transformed.reshape(4, 2)
        
        # Get bounding box
        min_x = max(0, int(pts[:, 0].min()))
        max_x = min(orig_w, int(pts[:, 0].max()))
        min_y = max(0, int(pts[:, 1].min()))
        max_y = min(orig_h, int(pts[:, 1].max()))
        
        return {"x": min_x, "y": min_y, "w": max_x - min_x, "h": max_y - min_y}

    def _preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        if roi.size == 0:
            return roi
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        return enhanced

    def _extract_name(self, results: List[OCRResult]) -> str:
        if not results:
            return ""
        best = max(results, key=lambda r: r.confidence)
        return best.text.strip() if best.confidence > 0.3 else ""

    def _extract_number(self, results: List[OCRResult]) -> str:
        for r in results:
            match = re.search(r'\d{1,3}\s*/\s*\d{1,3}', r.text)
            if match:
                return match.group().replace(' ', '')
        return ""

    def _extract_collection(self, results: List[OCRResult]) -> str:
        for r in results:
            match = re.search(r'\b([A-Z]{2,5})\b', r.text.upper())
            if match:
                code = match.group(1)
                if code not in ['THE', 'AND', 'FOR', 'HP', 'EX', 'GX', 'VMAX', 'VSTAR']:
                    return code
        return ""

    def _detect_language(self, results: List[OCRResult]) -> Optional[str]:
        text = " ".join([r.text.upper() for r in results])
        en = sum(1 for kw in self.ENGLISH_KW if kw in text)
        pt = sum(1 for kw in self.PORTUGUESE_KW if kw in text)
        if pt > en:
            return "pt"
        if en > 0:
            return "en"
        return None

    def _calc_confidence(self, title: List[OCRResult], bottom: List[OCRResult]) -> float:
        confs = [r.confidence for r in title + bottom]
        return round(sum(confs) / len(confs), 2) if confs else 0.0
