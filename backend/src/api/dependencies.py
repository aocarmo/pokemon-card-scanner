# FILE: src/api/dependencies.py
from application.use_cases import ScanCardUseCase
from infrastructure.vision import OpenCVCardDetector, OpenCVROIExtractor, TemplateSetClassifier
from infrastructure.ocr import EasyOCRService

_ocr_service = None
_set_classifier = None


def get_ocr_service():
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = EasyOCRService(languages=["en"], gpu=False)
    return _ocr_service


def get_set_classifier():
    global _set_classifier
    if _set_classifier is None:
        _set_classifier = TemplateSetClassifier(templates_dir="templates/sets")
    return _set_classifier


def get_scanner(debug: bool = False, debug_output_path: str = None) -> ScanCardUseCase:
    return ScanCardUseCase(
        detector=OpenCVCardDetector(output_size=(800, 1100)),
        roi_extractor=OpenCVROIExtractor(),
        ocr_service=get_ocr_service(),
        set_classifier=get_set_classifier(),
        debug=debug,
        debug_output_path=debug_output_path or "debug_output.jpg"
    )
