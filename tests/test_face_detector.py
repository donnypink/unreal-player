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
        """Returns False when no faces detected."""
        detector = FaceDetector()
        
        # Create a black frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock the entire cascade classifier
        mock_cascade = Mock()
        mock_cascade.detectMultiScale.return_value = ()
        detector._face_cascade = mock_cascade
        
        result = detector.detect(frame)
        
        assert result is False

    def test_detect_returns_true_when_face_found(self):
        """Returns True when faces detected."""
        detector = FaceDetector()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Mock face detection result
        mock_faces = np.array([[100, 100, 50, 50]])
        
        # Mock the entire cascade classifier
        mock_cascade = Mock()
        mock_cascade.detectMultiScale.return_value = mock_faces
        detector._face_cascade = mock_cascade
        
        result = detector.detect(frame)
        
        assert result is True

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
        
        result = detector.detect_continuous(mock_cap, duration_seconds=0.1, check_interval=0.05)
        
        assert result is False
