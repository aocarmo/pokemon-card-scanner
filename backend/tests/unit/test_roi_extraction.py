# FILE: tests/unit/test_roi_extraction.py
import numpy as np
import pytest

from domain.value_objects import ROI, CardROIs
from infrastructure.vision.opencv_roi_extractor import OpenCVROIExtractor


class TestROI:
    def test_to_absolute_converts_relative_coords(self):
        roi = ROI(0.1, 0.2, 0.5, 0.6)
        result = roi.to_absolute(800, 1100)
        assert result == (80, 220, 400, 660)

    def test_to_absolute_handles_full_image(self):
        roi = ROI(0.0, 0.0, 1.0, 1.0)
        result = roi.to_absolute(800, 1100)
        assert result == (0, 0, 800, 1100)


class TestCardROIs:
    def test_default_rois_are_valid(self):
        rois = CardROIs()
        assert 0 < rois.title.y_end < 0.2  # Title at top
        assert rois.number.y_start > 0.9   # Number at bottom


class TestOpenCVROIExtractor:
    def test_extract_returns_all_rois(self):
        extractor = OpenCVROIExtractor()
        img = np.zeros((1100, 800, 3), dtype=np.uint8)
        result = extractor.extract(img)
        assert "title" in result
        assert "number" in result
        assert "set_symbol" in result

    def test_extracted_rois_have_correct_dimensions(self):
        extractor = OpenCVROIExtractor()
        img = np.ones((1100, 800, 3), dtype=np.uint8) * 255
        rois = extractor.extract(img)
        # Title ROI should be wider than tall
        assert rois["title"].shape[1] > rois["title"].shape[0]
        # All ROIs should be non-empty
        for name, roi in rois.items():
            assert roi.size > 0, f"{name} ROI is empty"
