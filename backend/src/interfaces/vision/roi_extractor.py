# FILE: src/interfaces/vision/roi_extractor.py
from abc import ABC, abstractmethod
from typing import Dict
import numpy as np


class IROIExtractor(ABC):
    @abstractmethod
    def extract(self, warped_image: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract ROIs from warped card image."""
        pass
