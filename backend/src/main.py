# FILE: src/main.py
import sys
import cv2

from domain.entities import ScanResult
from domain.errors import CardNotDetectedError
from infrastructure.vision import OpenCVCardDetector, OpenCVROIExtractor, TemplateSetClassifier
from infrastructure.ocr import EasyOCRService
from application.use_cases import ScanCardUseCase


def create_scanner(debug: bool = False, debug_output: str = "debug_output.jpg") -> ScanCardUseCase:
    detector = OpenCVCardDetector(output_size=(800, 1100))
    roi_extractor = OpenCVROIExtractor()
    ocr_service = EasyOCRService(languages=["en"], gpu=False)
    set_classifier = TemplateSetClassifier(templates_dir="templates/sets")
    return ScanCardUseCase(
        detector=detector,
        roi_extractor=roi_extractor,
        ocr_service=ocr_service,
        set_classifier=set_classifier,
        debug=debug,
        debug_output_path=debug_output
    )


def scan_card(image_path: str, debug: bool = False) -> dict:
    image = cv2.imread(image_path)
    if image is None:
        return {"error": f"Could not read image: {image_path}"}

    scanner = create_scanner(debug=debug)
    try:
        result = scanner.execute(image)
        return result.to_dict()
    except CardNotDetectedError as e:
        return {"error": str(e), "name": "", "number": "", "confidence": 0.0}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <image_path> [--debug]")
        sys.exit(1)

    image_path = sys.argv[1]
    debug_mode = "--debug" in sys.argv

    result = scan_card(image_path, debug=debug_mode)
    print(result)

    if debug_mode:
        print("Debug image saved to: debug_output.jpg")
