# FILE: src/interfaces/ocr/ocr_service.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np


@dataclass
class OCRResult:
    text: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None


class IOCRService(ABC):
    @abstractmethod
    def read(self, image: np.ndarray) -> List[OCRResult]:
        """Read text from image, return list of results."""
        pass
