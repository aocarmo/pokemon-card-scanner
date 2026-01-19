# FILE: src/domain/errors/exceptions.py

class CardScannerError(Exception):
    """Base exception for card scanner."""
    pass


class CardNotDetectedError(CardScannerError):
    """Raised when no card contour is found."""
    pass


class OCRError(CardScannerError):
    """Raised when OCR fails."""
    pass
