# FILE: src/domain/value_objects/roi.py
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ROI:
    """Region of Interest as relative coordinates (0.0-1.0)."""
    x_start: float
    y_start: float
    x_end: float
    y_end: float

    def to_absolute(self, width: int, height: int) -> Tuple[int, int, int, int]:
        return (
            int(self.x_start * width),
            int(self.y_start * height),
            int(self.x_end * width),
            int(self.y_end * height),
        )


@dataclass(frozen=True)
class CardROIs:
    """Standard ROI definitions for Pokemon cards (after warp to 800x1100)."""
    title: ROI = ROI(0.05, 0.02, 0.85, 0.09)
    number: ROI = ROI(0.55, 0.94, 0.95, 0.99)
    set_symbol: ROI = ROI(0.02, 0.90, 0.20, 0.98)
