# FILE: src/infrastructure/vision/placeholder_set_classifier.py
from typing import Tuple
import numpy as np

from interfaces.vision import ISetSymbolClassifier


class PlaceholderSetClassifier(ISetSymbolClassifier):
    """Placeholder that always returns unknown."""
    def classify(self, symbol_image: np.ndarray) -> Tuple[str, float]:
        return ("unknown", 0.0)
