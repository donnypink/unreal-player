"""Camera management - separate from UI rendering."""
import cv2
import numpy as np
from typing import Optional, Tuple


class CameraManager:
    """Manages camera access and frame capture."""
    
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self._cap: Optional[cv2.VideoCapture] = None
        self.frame_width = 0
        self.frame_height = 0
    
    def open(self) -> bool:
        """Open camera and get frame dimensions."""
        self._cap = cv2.VideoCapture(self.camera_index)
        if not self._cap.isOpened():
            return False
        
        # Get frame dimensions
        ret, frame = self._cap.read()
        if ret:
            self.frame_height, self.frame_width = frame.shape[:2]
            print(f"[INFO] Camera opened: {self.frame_width}x{self.frame_height}")
            return True
        return False
    
    def release(self):
        """Release camera."""
        if self._cap:
            self._cap.release()
            self._cap = None
    
    def is_opened(self) -> bool:
        """Check if camera is open."""
        return self._cap is not None and self._cap.isOpened()
    
    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from camera."""
        if self.is_opened():
            ret, frame = self._cap.read()
            if ret:
                return frame
        return None
    
    def get_frame_size(self) -> Tuple[int, int]:
        """Get (width, height) of frames."""
        return (self.frame_width, self.frame_height)
