# FILE: src/interfaces/vision/set_classifier.py
from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class ISetSymbolClassifier(ABC):
    @abstractmethod
    def classify(self, symbol_image: np.ndarray) -> Tuple[str, float]:
        """Classify set symbol, return (set_code, confidence)."""
        pass
