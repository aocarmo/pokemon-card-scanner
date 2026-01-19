# FILE: src/interfaces/vision/card_detector.py
from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class ICardDetector(ABC):
    @abstractmethod
    def detect_and_warp(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Detect card and return perspective-corrected image."""
        pass
