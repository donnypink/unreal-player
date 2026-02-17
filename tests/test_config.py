"""Tests for Config class."""
import pytest
from config import Config


class TestConfig:
    """Tests for configuration management."""

    def test_loads_required_paths(self, mock_config_loader):
        """Config loads tracking and idle exe paths."""
        with mock_config_loader():
            config = Config("dummy.json")
            
            assert config.tracking_exe == "C:/test/tracking.exe"
            assert config.idle_exe == "C:/test/idle.exe"

    def test_uses_defaults_for_optional(self, mock_config_loader):
        """Config uses default values for optional settings."""
        with mock_config_loader():
            config = Config("dummy.json")
            
            assert config.camera_index == 0
            assert config.face_detection_confidence == 0.5
            assert config.detection_threshold_seconds == 3.0

    def test_allows_custom_face_confidence(self, mock_config_loader):
        """Config respects custom face detection confidence."""
        with mock_config_loader({"face_detection_confidence": 0.8}):
            config = Config("dummy.json")
            
            assert config.face_detection_confidence == 0.8

    def test_allows_custom_threshold_seconds(self, mock_config_loader):
        """Config respects custom detection threshold in seconds."""
        with mock_config_loader({"detection_threshold_seconds": 5.0}):
            config = Config("dummy.json")
            
            assert config.detection_threshold_seconds == 5.0

    def test_raises_on_missing_file(self):
        """Raises FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            Config("nonexistent.json")
