# FILE: tests/unit/test_perspective_transform.py
import numpy as np
import pytest

from infrastructure.vision.opencv_card_detector import OpenCVCardDetector


class TestOrderPoints:
    def test_orders_points_clockwise_from_top_left(self):
        detector = OpenCVCardDetector()
        # Scrambled points
        pts = np.array([[100, 0], [0, 0], [0, 100], [100, 100]], dtype=np.float32)
        result = detector._order_points(pts)
        expected = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.float32)
        np.testing.assert_array_equal(result, expected)

    def test_handles_rotated_rectangle(self):
        detector = OpenCVCardDetector()
        pts = np.array([[50, 0], [100, 50], [50, 100], [0, 50]], dtype=np.float32)
        result = detector._order_points(pts)
        assert result.shape == (4, 2)
        # Top-left has smallest sum
        assert result[0].sum() == pts.sum(axis=1).min()


class TestWarpPerspective:
    def test_warps_to_output_size(self):
        detector = OpenCVCardDetector(output_size=(800, 1100))
        # Create test image with known contour
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        contour = np.array([[50, 50], [450, 50], [450, 450], [50, 450]])
        result = detector._warp_perspective(img, contour)
        assert result.shape == (1100, 800, 3)
