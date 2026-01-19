# FILE: src/infrastructure/vision/opencv_card_detector.py
from typing import Optional, Tuple
import numpy as np
import cv2

from interfaces.vision import ICardDetector


class OpenCVCardDetector(ICardDetector):
    def __init__(self, output_size: Tuple[int, int] = (800, 1100)):
        self._output_size = output_size

    def detect_and_warp(self, image: np.ndarray) -> Optional[np.ndarray]:
        contour = self._find_card_contour(image)
        if contour is None:
            return None
        return self._warp_perspective(image, contour)

    def _find_card_contour(self, image: np.ndarray) -> Optional[np.ndarray]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                return approx
        return None

    def _warp_perspective(self, image: np.ndarray, contour: np.ndarray) -> np.ndarray:
        pts = contour.reshape(4, 2).astype(np.float32)
        rect = self._order_points(pts)
        dst = np.array([
            [0, 0],
            [self._output_size[0], 0],
            [self._output_size[0], self._output_size[1]],
            [0, self._output_size[1]]
        ], dtype=np.float32)
        M = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(image, M, self._output_size)

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect
