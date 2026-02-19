"""Tests for ModeDecider class."""
import time
import pytest
from mode_decider import ModeDecider


class TestModeDecider:
    """Tests for mode decision logic based on time."""

    def test_returns_idle_initially(self):
        """Returns 'idle' when no face has been seen."""
        decider = ModeDecider(threshold_seconds=3.0)
        result = decider.update(False)
        assert result == "idle"

    def test_returns_idle_while_face_not_long_enough(self):
        """Returns 'idle' when face seen but not long enough."""
        decider = ModeDecider(threshold_seconds=3.0)
        
        # Face detected but not for threshold duration
        decider.update(True)
        result = decider.update(True)  # Still not past threshold
        assert result == "idle"

    def test_returns_tracking_after_threshold(self):
        """Returns 'tracking' after face present for threshold duration."""
        decider = ModeDecider(threshold_seconds=0.1)
        
        decider.update(True)
        time.sleep(0.15)  # Wait past threshold
        result = decider.update(True)
        
        assert result == "tracking"

    def test_switches_to_idle_after_face_gone(self):
        """Switches to 'idle' after face gone for grace period + threshold."""
        decider = ModeDecider(threshold_seconds=0.1, grace_period=0.1)
        
        # First establish face presence
        decider.update(True)
        time.sleep(0.15)
        decider.update(True)  # Now in tracking mode
        
        # Face goes away
        time.sleep(0.15)  # Wait past grace period
        result = decider.update(False)
        
        assert result == "idle"

    def test_grace_period_allows_brief_detection_failures(self):
        """Brief detection failures don't reset the timer."""
        decider = ModeDecider(threshold_seconds=0.2, grace_period=0.3)
        
        # Face detected for 0.15s (not quite threshold)
        decider.update(True)
        time.sleep(0.15)
        
        # Brief failure (0.1s) - within grace period
        decider.update(False)
        time.sleep(0.1)
        
        # Face returns - timer should NOT have reset
        result = decider.update(True)
        # Should still be idle but with accumulated time
        assert decider.face_duration > 0.15  # Timer preserved

    def test_maintains_tracking_while_face_present(self):
        """Maintains 'tracking' while face continuously present."""
        decider = ModeDecider(threshold_seconds=0.1)
        
        decider.update(True)
        time.sleep(0.15)
        decider.update(True)  # Now tracking
        
        # Continue with face present
        result = decider.update(True)
        assert result == "tracking"

    def test_reset_clears_state(self):
        """Reset clears detection state."""
        decider = ModeDecider(threshold_seconds=0.1)
        
        decider.update(True)
        time.sleep(0.15)
        decider.update(True)  # Now tracking
        
        decider.reset()
        
        result = decider.update(False)
        assert result == "idle"
        assert decider.is_face_present is False

    def test_is_face_present_property(self):
        """is_face_present reflects confirmed detection state."""
        decider = ModeDecider(threshold_seconds=0.1)
        
        assert decider.is_face_present is False
        
        # Face detected but not confirmed yet
        decider.update(True)
        assert decider.is_face_present is False
        
        # After threshold, face is confirmed present
        time.sleep(0.15)
        decider.update(True)
        assert decider.is_face_present is True
        
        decider.reset()
        assert decider.is_face_present is False
