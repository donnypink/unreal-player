"""Mode decision logic based on face detection over time."""
import time


class ModeDecider:
    """Decides which mode to run based on face detection over time."""
    
    def __init__(self, threshold_seconds: float = 3.0, grace_period: float = 0.5):
        self.threshold_seconds = threshold_seconds
        self.grace_period = grace_period  # Time face can be "lost" before resetting
        self._face_first_seen = None
        self._face_last_seen = None
        self._confirmed_tracking = False
    
    def reset(self):
        """Clear detection state."""
        self._face_first_seen = None
        self._face_last_seen = None
        self._confirmed_tracking = False
    
    def update(self, face_detected: bool) -> str:
        """Update with detection result and return recommended mode."""
        current_time = time.time()
        
        if face_detected:
            self._face_last_seen = current_time
            
            if self._face_first_seen is None:
                self._face_first_seen = current_time
            
            # Check if face has been present long enough to confirm tracking
            elapsed = current_time - self._face_first_seen
            if elapsed >= self.threshold_seconds:
                self._confirmed_tracking = True
                return "tracking"
            
            # Face present but not long enough yet
            return "idle"
        else:
            # Face lost - check if it's been gone long enough to reset
            if self._face_last_seen is not None:
                time_since_face = current_time - self._face_last_seen
                if time_since_face < self.grace_period:
                    # Still within grace period, don't reset yet
                    # Check if we had enough time before to trigger tracking
                    if self._face_first_seen is not None:
                        elapsed = self._face_last_seen - self._face_first_seen
                        if elapsed >= self.threshold_seconds:
                            self._confirmed_tracking = True
                            return "tracking"
                    return "idle"
                else:
                    # Grace period exceeded, reset
                    if self._confirmed_tracking:
                        # Was tracking, now lost for too long
                        self._face_first_seen = None
                        self._confirmed_tracking = False
                        return "idle"
            
            # No face seen yet, or not gone long enough
            if not self._confirmed_tracking:
                self._face_first_seen = None
                return "idle"
        
        # Maintain current state
        return "tracking" if self._confirmed_tracking else "idle"
    
    @property
    def is_face_present(self) -> bool:
        """Check if face is currently considered present (confirmed)."""
        return self._confirmed_tracking
    
    @property
    def face_duration(self) -> float:
        """Get how long face has been detected (in seconds)."""
        if self._face_first_seen is None:
            return 0.0
        if self._face_last_seen is None:
            return 0.0
        # Use the last seen time to calculate duration (allows for grace period)
        return self._face_last_seen - self._face_first_seen
