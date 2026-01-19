# FILE: src/infrastructure/vision/opencv_roi_extractor.py
from typing import Dict
import numpy as np
import cv2

from interfaces.vision import IROIExtractor
from domain.value_objects import CardROIs


class OpenCVROIExtractor(IROIExtractor):
    def __init__(self, rois: CardROIs = CardROIs()):
        self._rois = rois

    def extract(self, warped_image: np.ndarray) -> Dict[str, np.ndarray]:
        h, w = warped_image.shape[:2]
        return {
            "title": self._crop(warped_image, self._rois.title.to_absolute(w, h)),
            "number": self._crop(warped_image, self._rois.number.to_absolute(w, h)),
            "set_symbol": self._crop(warped_image, self._rois.set_symbol.to_absolute(w, h)),
        }

    def _crop(self, image: np.ndarray, coords: tuple) -> np.ndarray:
        x1, y1, x2, y2 = coords
        return image[y1:y2, x1:x2]
