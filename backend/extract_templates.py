# Extract set symbol templates from card images
# Usage: python extract_templates.py <image_path> <set_code>
# Example: python extract_templates.py card_sv8pt5.jpg sv8pt5

import sys
import cv2
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.vision import OpenCVCardDetector, OpenCVROIExtractor


def extract_set_symbol(image_path: str, set_code: str):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read {image_path}")
        return

    detector = OpenCVCardDetector(output_size=(800, 1100))
    extractor = OpenCVROIExtractor()

    warped = detector.detect_and_warp(img)
    if warped is None:
        print("Error: No card detected")
        return

    rois = extractor.extract(warped)
    symbol = rois["set_symbol"]

    # Save template
    output_dir = Path("templates/sets") / set_code
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "template.png"
    cv2.imwrite(str(output_path), symbol)
    print(f"Saved: {output_path}")

    # Show preview
    cv2.imshow("Set Symbol", symbol)
    cv2.imshow("Warped Card", cv2.resize(warped, (400, 550)))
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_templates.py <image_path> <set_code>")
        print("Example: python extract_templates.py pikachu_sv8pt5.jpg sv8pt5")
        sys.exit(1)

    extract_set_symbol(sys.argv[1], sys.argv[2])
