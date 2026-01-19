# FILE: src/domain/entities/scan_result.py
from dataclasses import dataclass, asdict, field
from typing import List


@dataclass
class BoundingBox:
    label: str
    x: int
    y: int
    w: int
    h: int
    conf: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ScanResult:
    name: str
    number: str
    set: str
    language: str
    confidence: float
    boxes: tuple = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "number": self.number,
            "set": self.set,
            "language": self.language,
            "confidence": self.confidence,
            "boxes": [b.to_dict() if hasattr(b, 'to_dict') else b for b in self.boxes]
        }

    @staticmethod
    def empty() -> "ScanResult":
        return ScanResult(name="", number="", set="unknown", language="unknown", confidence=0.0, boxes=())
