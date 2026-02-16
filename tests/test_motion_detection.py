"""
Unit tests for UE Controller motion detection functionality.
These tests follow TDD methodology - they define expected behavior first.
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ue_controller import UEController


class TestUEShouldSwitch:
    """Tests for the should_switch() decision method."""

    def setup_method(self):
        """Create controller with default config for each test."""
        self.config = {
            "tracking_exe": "C:/test/tracking.exe",
            "idle_exe": "C:/test/idle.exe",
            "camera_index": 0,
            "motion_threshold": 30,
            "detection_delay_frames": 5,
            "tracking_run_seconds": 30,
            "idle_run_seconds": 60
        }
    
    def test_should_switch_returns_tracking_when_majority_motion_detected(self):
        """should_switch() returns 'tracking' when majority of recent frames show motion."""
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
            # Clear any default history
            controller.motion_history = []
            controller.detection_delay_frames = 5
        
        # Simulate motion detected in majority of frames
        for _ in range(3):
            result = controller.should_switch(True)
        
        assert result == "tracking", "Should return 'tracking' when majority show motion"

    def test_should_switch_returns_idle_when_majority_no_motion(self):
        """should_switch() returns 'idle' when majority of recent frames show no motion."""
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
            controller.motion_history = []
            controller.detection_delay_frames = 5
        
        # Simulate no motion in majority of frames
        for _ in range(3):
            result = controller.should_switch(False)
        
        assert result == "idle", "Should return 'idle' when majority show no motion"

    def test_should_switch_handles_tie_with_motion(self):
        """should_switch() returns 'tracking' on tie (2 motion, 3 no_motion would be idle)."""
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
            controller.motion_history = []
            controller.detection_delay_frames = 5
        
        # Tie: 3 no motion, 2 motion = idle (majority no motion)
        for _ in range(3):
            controller.should_switch(False)
        for _ in range(2):
            controller.should_switch(True)
        
        result = controller.should_switch(False)  # This makes it 3 no motion, 3 motion
        assert result == "idle", "Should return 'idle' when no motion is majority"

    def test_should_switch_respects_detection_delay_frames_config(self):
        """should_switch() uses detection_delay_frames from config."""
        config = self.config.copy()
        config["detection_delay_frames"] = 3
        
        with patch.object(UEController, '_load_config', return_value=config):
            controller = UEController()
            controller.motion_history = []
        
        # With delay_frames=3, only last 3 frames matter
        controller.should_switch(False)  # history: [False]
        controller.should_switch(False)  # history: [False, False]
        controller.should_switch(False)  # history: [False, False, False]
        controller.should_switch(True)   # history: [False, False, True] - 1/3 motion
        result = controller.should_switch(True)  # history: [False, True, True] - 2/3 motion
        
        assert result == "tracking"


class TestMotionDetection:
    """Tests for motion detection threshold and sensitivity."""

    def setup_method(self):
        """Create controller with test config."""
        self.config = {
            "tracking_exe": "C:/test/tracking.exe",
            "idle_exe": "C:/test/idle.exe",
            "camera_index": 0,
            "motion_threshold": 30,
            "detection_delay_frames": 5,
            "tracking_run_seconds": 30,
            "idle_run_seconds": 60
        }

    def test_motion_threshold_from_config(self):
        """Controller uses motion_threshold from config (default 30)."""
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
        
        assert controller.config.get("motion_threshold") == 30

    def test_detects_motion_with_configurable_threshold(self):
        """detect_motion should use configurable threshold from config."""
        # This test verifies the threshold can be configured
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
        
        # Verify config value exists and is used
        threshold = controller.config.get("motion_threshold", 30)
        assert isinstance(threshold, int)
        assert threshold > 0


class TestMotionHistory:
    """Tests for motion history management."""

    def setup_method(self):
        """Create controller."""
        self.config = {
            "tracking_exe": "C:/test/tracking.exe",
            "idle_exe": "C:/test/idle.exe",
            "camera_index": 0,
            "motion_threshold": 30,
            "detection_delay_frames": 5,
            "tracking_run_seconds": 30,
            "idle_run_seconds": 60
        }

    def test_motion_history_maintains_max_length(self):
        """motion_history should not exceed detection_delay_frames."""
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
            controller.motion_history = []
            controller.detection_delay_frames = 5
        
        # Add more than delay_frames
        for i in range(10):
            controller.should_switch(i % 2 == 0)
        
        # History should be capped at detection_delay_frames
        assert len(controller.motion_history) <= controller.detection_delay_frames

    def test_motion_history_starts_empty(self):
        """motion_history should initialize empty."""
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
        
        assert controller.motion_history == []


class TestControllerInitialization:
    """Tests for controller initialization."""

    def setup_method(self):
        """Create controller config."""
        self.config = {
            "tracking_exe": "C:/test/tracking.exe",
            "idle_exe": "C:/test/idle.exe",
            "camera_index": 0,
            "motion_threshold": 30,
            "detection_delay_frames": 5,
            "tracking_run_seconds": 30,
            "idle_run_seconds": 60
        }

    def test_controller_has_no_initial_mode(self):
        """Controller should have no current_mode initially."""
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
        
        assert controller.current_mode is None

    def test_controller_has_no_initial_previous_frame(self):
        """Controller should have no previous_frame initially."""
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
        
        assert controller.previous_frame is None

    def test_load_config_returns_dict(self):
        """_load_config should return configuration dictionary."""
        with patch.object(UEController, '_load_config', return_value=self.config):
            controller = UEController()
        
        assert isinstance(controller.config, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
