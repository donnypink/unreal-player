"""Tests for FaceDetector class."""
import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np
from face_detector import FaceDetector


class TestFaceDetector:
    """Tests for face detection functionality."""

    def test_uses_configurable_confidence(self):
        """Detector uses configurable confidence."""
        detector = FaceDetector(min_confidence=0.8)
        assert detector.min_confidence == 0.8

    def test_uses_default_confidence(self):
        """Detector uses default confidence of 0.5."""
        detector = FaceDetector()
        assert detector.min_confidence == 0.5

    def test_detect_returns_false_when_no_faces(self):
        """Returns (False, []) when no faces detected."""
        detector = FaceDetector()
        
        # Create a black frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock the entire cascade classifier
        mock_cascade = Mock()
        mock_cascade.detectMultiScale.return_value = ()
        detector._face_cascade = mock_cascade
        
        face_found, face_rects = detector.detect(frame)
        
        assert face_found is False
        assert face_rects == []

    def test_detect_returns_true_when_face_found(self):
        """Returns (True, face_rects) when faces detected."""
        detector = FaceDetector()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Mock face detection result
        mock_faces = np.array([[100, 100, 50, 50]])
        
        # Mock the entire cascade classifier
        mock_cascade = Mock()
        mock_cascade.detectMultiScale.return_value = mock_faces
        detector._face_cascade = mock_cascade
        
        face_found, face_rects = detector.detect(frame)
        
        assert face_found is True
        assert len(face_rects) > 0

    def test_detect_continuous_checks_for_duration(self):
        """detect_continuous checks for faces over specified duration."""
        detector = FaceDetector()
        
        # Mock the cascade to return no faces
        mock_cascade = Mock()
        mock_cascade.detectMultiScale.return_value = ()
        detector._face_cascade = mock_cascade
        
        # Mock VideoCapture
        mock_cap = Mock()
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        
        face_found, face_rects = detector.detect_continuous(mock_cap, duration_seconds=0.1, check_interval=0.05)
        
        assert face_found is False
        assert face_rects == []

    def test_detect_respects_boundary_check(self):
        """Detector respects boundary check callback."""
        detector = FaceDetector()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Mock face outside boundary at (10, 10)
        mock_faces = np.array([[10, 10, 50, 50]])
        
        mock_cascade = Mock()
        mock_cascade.detectMultiScale.return_value = mock_faces
        detector._face_cascade = mock_cascade
        
        # Set boundary check that rejects faces at x < 50
        def boundary_check(rect):
            x, y, w, h = rect
            return x >= 50
        
        detector.set_boundary_check(boundary_check)
        
        face_found, face_rects = detector.detect(frame)
        
        # Face should be detected but not valid (outside boundary)
        assert len(face_rects) == 1  # Face was found
        assert face_found is False   # But not within valid boundary

    def test_detect_accepts_face_in_boundary(self):
        """Detector accepts face within boundary."""
        detector = FaceDetector()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Mock face inside boundary at (100, 100)
        mock_faces = np.array([[100, 100, 50, 50]])
        
        mock_cascade = Mock()
        mock_cascade.detectMultiScale.return_value = mock_faces
        detector._face_cascade = mock_cascade
        
        # Set boundary check that accepts faces at x >= 50
        def boundary_check(rect):
            x, y, w, h = rect
            return x >= 50
        
        detector.set_boundary_check(boundary_check)
        
        face_found, face_rects = detector.detect(frame)
        
        # Face should be detected AND valid
        assert len(face_rects) == 1
        assert face_found is True
