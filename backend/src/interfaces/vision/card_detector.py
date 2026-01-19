# FILE: src/interfaces/vision/card_detector.py
from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class ICardDetector(ABC):
    @abstractmethod
    def detect_and_warp(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Detect card and return perspective-corrected image."""
        pass

    @abstractmethod
    def find_card_contour(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Find card contour in original image coordinates."""
        pass

    @abstractmethod
    def warp_from_contour(self, image: np.ndarray, contour: np.ndarray) -> np.ndarray:
        """Warp image using provided contour."""
        pass
