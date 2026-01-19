# FILE: src/domain/entities/scan_result.py
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ScanResult:
    name: str
    number: str
    set: str
    confidence: float

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def empty() -> "ScanResult":
        return ScanResult(name="", number="", set="unknown", confidence=0.0)
