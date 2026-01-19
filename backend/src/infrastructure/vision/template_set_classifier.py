# FILE: src/infrastructure/vision/template_set_classifier.py
# Template folder structure:
#   templates/sets/
#     ├── sv8pt5/template.png   (Prismatic Evolutions)
#     ├── sv8/template.png      (Surging Sparks)
#     └── base1/template.png    (Base Set)
from typing import Tuple, Dict
from pathlib import Path
import numpy as np
import cv2

from interfaces.vision import ISetSymbolClassifier


class TemplateSetClassifier(ISetSymbolClassifier):
    def __init__(self, templates_dir: str = "templates/sets"):
        self._templates: Dict[str, np.ndarray] = {}
        self._load_templates(Path(templates_dir))

    def _load_templates(self, templates_dir: Path):
        if not templates_dir.exists():
            return
        for set_dir in templates_dir.iterdir():
            if set_dir.is_dir():
                template_path = set_dir / "template.png"
                if template_path.exists():
                    img = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        self._templates[set_dir.name] = img

    def classify(self, symbol_image: np.ndarray) -> Tuple[str, float]:
        if not self._templates:
            return ("unknown", 0.0)

        if len(symbol_image.shape) == 3:
            gray = cv2.cvtColor(symbol_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = symbol_image

        best_match = ("unknown", 0.0)
        for set_code, template in self._templates.items():
            resized = cv2.resize(gray, (template.shape[1], template.shape[0]))
            result = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val > best_match[1]:
                best_match = (set_code, float(max_val))

        if best_match[1] < 0.5:
            return ("unknown", best_match[1])
        return best_match
