"""Shared test fixtures and configuration."""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import Config


@pytest.fixture
def test_config():
    """Default test configuration."""
    return {
        "tracking_exe": "C:/test/tracking.exe",
        "idle_exe": "C:/test/idle.exe",
        "detection_camera_index": 0,
        "face_detection_confidence": 0.5,
        "detection_threshold_seconds": 3.0,
        "face_loss_grace_period": 2.0
    }


@pytest.fixture
def mock_config_loader(test_config):
    """Factory for creating mocked config loaders."""
    def _loader(config_overrides=None):
        config = test_config.copy()
        if config_overrides:
            config.update(config_overrides)
        return patch.object(Config, '_load', return_value=config)
    return _loader
